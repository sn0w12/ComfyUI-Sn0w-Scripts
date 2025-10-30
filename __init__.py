import importlib
import json
import os
from server import PromptServer
from aiohttp import web

from .src.dynamic_lora_loader import generate_lora_node_class
from .src.dynamic_scheduler_loader import generate_scheduler_node_class
from .src.check_folder_paths import check_lora_folders
from .sn0w import CharacterLoader, ConfigReader, Logger

from .src.lora_selector import LoraSelectorNode
from .src.lora_tester import LoraTestNode
from .src.character_select import CharacterSelectNode
from .src.prompt_combine import CombineStringNode
from .src.lora_stacker import LoraStackerNode
from .src.get_font_size import GetFontSizeNode
from .src.prompt_selector import PromptSelectNode
from .src.upscale_with_model_by import UpscaleImageBy
from .src.load_lora_from_folder import LoadLoraFolderNode
from .src.textbox import TextboxNode
from .src.simple_ksampler import SimpleSamplerCustom
from .src.filter_tags import FilterTags
from .src.generate_all_character_images import GenerateCharactersNode
from .src.upscaler import AutoTaggedTiledUpscaler

# Constants
WEB_DIRECTORY = "./web"
CURRENT_UNIQUE_ID = 0  # Global variable to track the unique ID
logger = Logger()

NODE_CLASS_MAPPINGS = {
    "Lora Selector": LoraSelectorNode,
    "Lora Tester": LoraTestNode,
    "Character Selector": CharacterSelectNode,
    "Prompt Combine": CombineStringNode,
    "Sn0w Lora Stacker": LoraStackerNode,
    "Load Lora Sn0w": generate_lora_node_class("loras"),
    "Get Font Size": GetFontSizeNode,
    "Prompt Selector": PromptSelectNode,
    "Upscale Image With Model By": UpscaleImageBy,
    "Load Lora Folder": LoadLoraFolderNode,
    "Copy/Paste Textbox": TextboxNode,
    "Sn0w KSampler": SimpleSamplerCustom,
    "Filter Tags": FilterTags,
    "Generate All Characters": GenerateCharactersNode,
    "TaggedTiledUpscaler": AutoTaggedTiledUpscaler,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Lora Selector": "Lora Selector",
    "Lora Tester": "Lora Tester",
    "Character Selector": "Character Selector",
    "Prompt Combine": "Prompt Combine",
    "Sn0w Lora Stacker": "Sn0w Lora Stacker",
    "Load Lora Sn0w": "Load Lora Sn0w",
    "Get Font Size": "Get Font Size",
    "Prompt Selector": "Prompt Selector",
    "Upscale Image With Model By": "Upscale Image With Model By",
    "Load Lora Folder": "Load Lora Folder",
    "Copy/Paste Textbox": "Textbox",
    "Sn0w KSampler": "Sn0w KSampler",
    "Filter Tags": "Filter Tags",
    "Generate All Characters": "Generate All Character Images",
    "TaggedTiledUpscaler": "Tagged Tiled Upscaler",
}

# Function to check required folder paths
check_lora_folders()


def parse_custom_lora_loaders(custom_lora_loaders):
    """
    Parse a string of custom Lora loaders into a list of tuples containing
    the name, required folders, and the number of combinations.
    """
    required_folders_with_names = []
    entries = custom_lora_loaders.split("\n")
    for entry in entries:
        if entry.strip():
            name, _, remainder = entry.partition(":")
            if ":" in remainder:
                value, _, combos = remainder.partition(":")
            else:
                value = remainder
                combos = 1
            required_folders_with_names.append((name.strip(), value.strip().split(","), int(combos)))
    return required_folders_with_names


def generate_and_register_lora_node(lora_type, setting):
    """Generate and register the users custom lora loaders"""
    global CURRENT_UNIQUE_ID

    custom_lora_loaders = ConfigReader.get_setting(setting, None)
    if custom_lora_loaders is not None:
        required_folders_with_names = parse_custom_lora_loaders(custom_lora_loaders)
        for name, folders, combos in required_folders_with_names:
            CURRENT_UNIQUE_ID += 1
            unique_id_with_name = f"{name}_{CURRENT_UNIQUE_ID}"

            logger.log(f"Adding custom lora loader. Path: {folders}, Name: {name}, Inputs: {combos}", "INFORMATIONAL")
            DynamicLoraNode = generate_lora_node_class(lora_type, folders, combos)
            if DynamicLoraNode:
                if name in NODE_CLASS_MAPPINGS:
                    NODE_CLASS_MAPPINGS[unique_id_with_name] = DynamicLoraNode
                    NODE_DISPLAY_NAME_MAPPINGS[unique_id_with_name] = f"{name}"
                else:
                    NODE_CLASS_MAPPINGS[name] = DynamicLoraNode
                    NODE_DISPLAY_NAME_MAPPINGS[name] = f"{name}"


def generate_and_register_all_lora_nodes():
    """Generate and register all custom lora nodes."""
    lora_types = [
        ("loras_xl", "sn0w.CustomLoraLoaders.XL"),
        ("loras_15", "sn0w.CustomLoraLoaders"),
        ("loras_3", "sn0w.CustomLoraLoaders.3"),
    ]
    for lora_type, setting in lora_types:
        generate_and_register_lora_node(lora_type, setting)


def import_and_register_scheduler_nodes():
    """
    Import and register custom scheduler nodes from Python files in the
    'src/custom_schedulers' directory.
    """
    custom_schedulers_path = os.path.join(os.path.dirname(__file__), "src", "custom_schedulers")
    for filename in os.listdir(custom_schedulers_path):
        if filename.endswith(".py") and filename != "custom_schedulers.py":
            module_name = filename[:-3]
            module = import_module_from_path(module_name, os.path.join(custom_schedulers_path, filename))
            register_scheduler_node(module)


def import_module_from_path(module_name, file_path):
    """Helper function to import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def register_scheduler_node(module):
    """Register a scheduler node if it contains settings and a get_sigmas function."""
    settings = getattr(module, "settings", None)
    get_sigmas_function = getattr(module, "get_sigmas", None)
    if settings and get_sigmas_function:
        DynamicSchedulerNode = generate_scheduler_node_class(settings, get_sigmas_function)
        class_name = settings.get("name", "default").capitalize() + "Scheduler"
        NODE_CLASS_MAPPINGS[class_name] = DynamicSchedulerNode
        NODE_DISPLAY_NAME_MAPPINGS[class_name] = class_name


# Register custom nodes
generate_and_register_all_lora_nodes()
import_and_register_scheduler_nodes()

API_PREFIX = "/sn0w"


def get_all_series():
    return CharacterLoader.get_all_series()


@PromptServer.instance.routes.get(f"{API_PREFIX}/series")
async def series_endpoint(request):
    return web.json_response({"series": get_all_series()})


@PromptServer.instance.routes.get(f"{API_PREFIX}/visible_series")
async def get_visible_series(request):
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "web/settings/visible_series.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return web.json_response({"visible_series": data})
    return web.json_response({"visible_series": []})


@PromptServer.instance.routes.post(f"{API_PREFIX}/visible_series")
async def set_visible_series(request):
    data = await request.json()
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "web/settings/visible_series.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data.get("visible_series", []), f)
    return web.json_response({"status": "ok"})


@PromptServer.instance.routes.get(f"{API_PREFIX}/series/{{series}}/characters")
async def get_characters_by_series_endpoint(request):
    series = request.match_info.get("series", "")
    if not series:
        return web.json_response({"error": "Series name is required"}, status=400)
    characters = CharacterLoader.get_characters_by_series(series)
    return web.json_response({"series": series, "characters": characters})


@PromptServer.instance.routes.get(f"{API_PREFIX}/series_selector")
async def serve_series_selector(request):
    html = """
    <html>
    <head>
        <title>Select Series</title>
        <style>
            body {
                font-family: 'Segoe UI', Arial, sans-serif;
                background: #181a20;
                margin: 0;
                padding: 0;
                color: #e6e6e6;
            }
            .container {
                max-width: 520px;
                margin: 48px auto;
                background: #23242b;
                border-radius: 14px;
                padding: 36px 28px 28px 28px;
            }
            h2 {
                margin-top: 0;
                color: #fff;
                font-size: 1.6em;
                margin-bottom: 0px;
                letter-spacing: 0.5px;
            }
            #series-list {
                border-radius: 8px;
                padding: 10px 0 0 0;
                background: transparent;
                border: none;
                max-height: calc(100vh - 300px);
                overflow: auto;
            }
            label {
                display: flex;
                align-items: center;
                font-size: 1.13em;
                cursor: pointer;
                border-radius: 6px;
                transition: background 0.15s;
            }
            label:hover {
                background: #292b33;
            }
            input[type="checkbox"] {
                margin-right: 12px;
                accent-color: #4fa3ff;
                width: 18px;
                height: 18px;
            }
            button {
                background-color: #4fa3ff;
                color: #fff;
                border: none;
                border-radius: 6px;
                padding: 12px 28px;
                font-size: 1.08em;
                cursor: pointer;
                font-weight: 500;
                transition: background 0.2s;
            }
            button:hover {
                background-color: #2366d1;
            }
            #result {
                margin-top: 18px;
                color: #4fa3ff;
                font-weight: bold;
                min-height: 24px;
                letter-spacing: 0.2px;
            }
            @media (max-width: 600px) {
                .container {
                    max-width: 98vw;
                    padding: 18px 4vw 18px 4vw;
                }
                h2 {
                    font-size: 1.2em;
                }
                label {
                    font-size: 1em;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Select Series to Show in Dropdown</h2>
            <div id="series-list"></div>
            <button onclick="save()">Save</button>
            <div id="result"></div>
        </div>
        <script>
        let allSeries = [];
        function load() {
            fetch('/sn0w/series').then(r=>r.json()).then(data=>{
                allSeries = data.series;
                fetch('/sn0w/visible_series').then(r2=>r2.json()).then(vs=>{
                    let div = document.getElementById('series-list');
                    div.innerHTML = '';
                    let visible = vs.visible_series;
                    // If none selected, select all by default
                    if (!visible || visible.length === 0) visible = allSeries;
                    allSeries.forEach(s=>{
                        let checked = visible.includes(s) ? 'checked' : '';
                        // Create the Danbooru link
                        let tag = encodeURIComponent(s.replace(/ /g, "_"));
                        let link = `<a href="https://danbooru.donmai.us/posts?tags=${tag}" target="_blank" style="margin-left:8px;color:#4fa3ff;text-decoration:underline;font-size:0.95em;">link</a>`;
                        div.innerHTML += `<label><input type="checkbox" value="${s}" ${checked}>${s}${link}</label>`;
                    });
                });
            });
        }
        function save() {
            let cbs = document.querySelectorAll('#series-list input[type=checkbox]');
            let vals = [];
            cbs.forEach(cb=>{ if(cb.checked) vals.push(cb.value); });
            fetch('/sn0w/visible_series', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({visible_series: vals})
            }).then(r=>r.json()).then(data=>{
                document.getElementById('result').innerText = 'Saved!';
            });
        }
        window.onload = load;
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type="text/html")
