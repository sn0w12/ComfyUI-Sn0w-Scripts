# https://huggingface.co/spaces/SmilingWolf/wd-v1-4-tags
# https://github.com/pythongosssss/ComfyUI-WD14-Tagger

import comfy.utils
import asyncio
import aiohttp
import numpy as np
import csv
import os
import onnxruntime as ort
from onnxruntime import InferenceSession
from PIL import Image
from server import PromptServer
from aiohttp import web
import folder_paths
from tqdm import tqdm

# Default config settings
defaults = {
    "model": "wd-v1-4-moat-tagger-v2",
    "threshold": 0.35,
    "character_threshold": 0.85,
    "replace_underscore": False,
    "trailing_comma": False,
    "exclude_tags": "",
    "ortProviders": ["CPUExecutionProvider"],  # Changed to CPU-only by default
    "HF_ENDPOINT": "https://huggingface.co",
}

# Model definitions
models = {
    "wd-eva02-large-tagger-v3": "{HF_ENDPOINT}/SmilingWolf/wd-eva02-large-tagger-v3",
    "wd-vit-tagger-v3": "{HF_ENDPOINT}/SmilingWolf/wd-vit-tagger-v3",
    "wd-swinv2-tagger-v3": "{HF_ENDPOINT}/SmilingWolf/wd-swinv2-tagger-v3",
    "wd-convnext-tagger-v3": "{HF_ENDPOINT}/SmilingWolf/wd-convnext-tagger-v3",
    "wd-v1-4-moat-tagger-v2": "{HF_ENDPOINT}/SmilingWolf/wd-v1-4-moat-tagger-v2",
    "wd-v1-4-convnextv2-tagger-v2": "{HF_ENDPOINT}/SmilingWolf/wd-v1-4-convnextv2-tagger-v2",
    "wd-v1-4-convnext-tagger-v2": "{HF_ENDPOINT}/SmilingWolf/wd-v1-4-convnext-tagger-v2",
    "wd-v1-4-convnext-tagger": "{HF_ENDPOINT}/SmilingWolf/wd-v1-4-convnext-tagger",
    "wd-v1-4-vit-tagger-v2": "{HF_ENDPOINT}/SmilingWolf/wd-v1-4-vit-tagger-v2",
    "wd-v1-4-swinv2-tagger-v2": "{HF_ENDPOINT}/SmilingWolf/wd-v1-4-swinv2-tagger-v2",
    "wd-v1-4-vit-tagger": "{HF_ENDPOINT}/SmilingWolf/wd-v1-4-vit-tagger",
    "Z3D-E621-Convnext": "{HF_ENDPOINT}/silveroxides/Z3D-E621-Convnext",
}

# Determine models directory
if "wd14_tagger" in folder_paths.folder_names_and_paths:
    models_dir = folder_paths.get_folder_paths("wd14_tagger")[0]
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
else:
    # Use extension directory if folder paths not defined
    ext_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    models_dir = os.path.join(ext_dir, "models")
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)

print(f"WD14Tagger: Available ORT providers: {', '.join(ort.get_available_providers())}")
print(f"WD14Tagger: Using ORT providers: {', '.join(defaults['ortProviders'])}")


def get_installed_models():
    """Get a list of installed ONNX models with matching CSV files"""
    if not os.path.exists(models_dir):
        return []
    models_list = filter(lambda x: x.endswith(".onnx"), os.listdir(models_dir))
    models_list = [m for m in models_list if os.path.exists(os.path.join(models_dir, os.path.splitext(m)[0] + ".csv"))]
    return models_list


known_models = list(models.keys())


async def download_to_file(url, destination, update_callback=None, session=None):
    """Download a file from URL to the destination with progress tracking"""
    close_session = False
    if session is None:
        close_session = True
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        session = aiohttp.ClientSession(loop=loop)

    try:
        proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
        proxy_auth = None
        if proxy:
            proxy_auth = aiohttp.BasicAuth(os.getenv("PROXY_USER", ""), os.getenv("PROXY_PASS", ""))

        async with session.get(url, proxy=proxy, proxy_auth=proxy_auth) as response:
            size = int(response.headers.get("content-length", 0)) or None

            with tqdm(
                unit="B",
                unit_scale=True,
                miniters=1,
                desc=url.split("/")[-1],
                total=size,
            ) as progressbar:
                with open(destination, mode="wb") as f:
                    perc = 0
                    async for chunk in response.content.iter_chunked(2048):
                        f.write(chunk)
                        progressbar.update(len(chunk))
                        if update_callback is not None and progressbar.total is not None and progressbar.total != 0:
                            last = perc
                            perc = round(progressbar.n / progressbar.total, 2)
                            if perc != last:
                                last = perc
                                await update_callback(perc)
    finally:
        if close_session and session is not None:
            await session.close()


def wait_for_async(async_fn):
    """Run an async function and wait for the result"""
    return asyncio.run(async_fn())


def update_node_status(client_id, node, text, progress=None):
    """Update node status in the UI with progress information"""
    if client_id is None:
        client_id = getattr(PromptServer.instance, "client_id", None)

    if client_id is None:
        return

    PromptServer.instance.send_sync("status_update", {"node": node, "progress": progress, "text": text}, client_id)


async def tag(
    image,
    model_name,
    threshold=0.35,
    character_threshold=0.85,
    exclude_tags="",
    replace_underscore=True,
    trailing_comma=False,
    client_id=None,
    node=None,
):
    """Tag an image with the WD14 tagger model"""
    if model_name.endswith(".onnx"):
        model_name = model_name[0:-5]
    installed = list(get_installed_models())
    if not any(model_name + ".onnx" in s for s in installed):
        await download_model(model_name, client_id, node)

    name = os.path.join(models_dir, model_name + ".onnx")
    model = InferenceSession(name, providers=defaults["ortProviders"])

    input = model.get_inputs()[0]
    height = input.shape[1]

    # Reduce to max size and pad with white
    ratio = float(height) / max(image.size)
    new_size = tuple([int(x * ratio) for x in image.size])
    image = image.resize(new_size, Image.LANCZOS)
    square = Image.new("RGB", (height, height), (255, 255, 255))
    square.paste(image, ((height - new_size[0]) // 2, (height - new_size[1]) // 2))

    image = np.array(square).astype(np.float32)
    image = image[:, :, ::-1]  # RGB -> BGR
    image = np.expand_dims(image, 0)

    # Read all tags from csv and locate start of each category
    tags = []
    general_index = None
    character_index = None
    with open(os.path.join(models_dir, model_name + ".csv")) as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if general_index is None and row[2] == "0":
                general_index = reader.line_num - 2
            elif character_index is None and row[2] == "4":
                character_index = reader.line_num - 2
            if replace_underscore:
                tags.append(row[1].replace("_", " "))
            else:
                tags.append(row[1])

    label_name = model.get_outputs()[0].name
    probs = model.run([label_name], {input.name: image})[0]

    result = list(zip(tags, probs[0]))

    # rating = max(result[:general_index], key=lambda x: x[1])
    general = [item for item in result[general_index:character_index] if item[1] > threshold]
    character = [item for item in result[character_index:] if item[1] > character_threshold]

    all = character + general
    remove = [s.strip() for s in exclude_tags.lower().split(",")]
    all = [tag for tag in all if tag[0] not in remove]

    res = ("" if trailing_comma else ", ").join(
        (item[0].replace("(", "\\(").replace(")", "\\)") + (", " if trailing_comma else "") for item in all)
    )

    return res


async def download_model(model, client_id, node):
    """Download ONNX model and CSV file from HuggingFace"""
    hf_endpoint = os.getenv("HF_ENDPOINT", defaults["HF_ENDPOINT"])
    if not hf_endpoint.startswith("https://"):
        hf_endpoint = f"https://{hf_endpoint}"
    if hf_endpoint.endswith("/"):
        hf_endpoint = hf_endpoint.rstrip("/")

    url = models[model]
    url = url.replace("{HF_ENDPOINT}", hf_endpoint)
    url = f"{url}/resolve/main/"
    async with aiohttp.ClientSession(loop=asyncio.get_event_loop()) as session:

        async def update_callback(perc):
            message = ""
            if perc < 100:
                message = f"Downloading {model}"
            update_node_status(client_id, node, message, perc)

        try:
            await download_to_file(
                f"{url}model.onnx", os.path.join(models_dir, f"{model}.onnx"), update_callback, session=session
            )
            await download_to_file(
                f"{url}selected_tags.csv", os.path.join(models_dir, f"{model}.csv"), update_callback, session=session
            )
        except aiohttp.client_exceptions.ClientConnectorError as err:
            print(
                "Unable to download model. Download files manually or try using a HF mirror/proxy website by setting the environment variable HF_ENDPOINT=https://....."
            )
            raise

        update_node_status(client_id, node, None)

    return web.Response(status=200)


class WD14Tagger:
    @classmethod
    def INPUT_TYPES(s):
        extra = [name for name, _ in (os.path.splitext(m) for m in get_installed_models()) if name not in known_models]
        models = known_models + extra
        return {
            "required": {
                "image": ("IMAGE",),
                "model": (models, {"default": defaults["model"]}),
                "threshold": ("FLOAT", {"default": defaults["threshold"], "min": 0.0, "max": 1, "step": 0.05}),
                "character_threshold": (
                    "FLOAT",
                    {"default": defaults["character_threshold"], "min": 0.0, "max": 1, "step": 0.05},
                ),
                "replace_underscore": ("BOOLEAN", {"default": defaults["replace_underscore"]}),
                "trailing_comma": ("BOOLEAN", {"default": defaults["trailing_comma"]}),
                "exclude_tags": ("STRING", {"default": defaults["exclude_tags"]}),
            }
        }

    RETURN_TYPES = ("STRING",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "tag"
    OUTPUT_NODE = True

    CATEGORY = "image"

    def tag(
        self,
        image,
        model,
        threshold,
        character_threshold,
        exclude_tags="",
        replace_underscore=False,
        trailing_comma=False,
    ):
        tensor = image * 255
        tensor = np.array(tensor, dtype=np.uint8)

        pbar = comfy.utils.ProgressBar(tensor.shape[0])
        tags = []
        for i in range(tensor.shape[0]):
            image = Image.fromarray(tensor[i])
            tags.append(
                wait_for_async(
                    lambda: tag(
                        image, model, threshold, character_threshold, exclude_tags, replace_underscore, trailing_comma
                    )
                )
            )
            pbar.update(1)
        return (tags,)
