import { SettingUtils } from "./sn0w.js";
import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

async function addLoraLoaders(loraLoaders) {
    try {
        const response = await api.fetchApi(`${SettingUtils.API_PREFIX}/add_lora_loaders`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(loraLoaders),
        });

        const data = await response.json();
        SettingUtils.logSn0w("Lora Loaders successfully added.", "informational", "lora", data.message);
    } catch (error) {
        SettingUtils.logSn0w(error.message, "error");
    }
}

const settingDefinitions = [
    {
        id: "sn0w.HighlightFavourite",
        category: ["sn0w", "ContextMenu", "Highlight Favourite Items"],
        name: "Highlight Favourite Items",
        defaultValue: false,
        type: "boolean",
    },
    {
        id: "sn0w.previewImageDelay",
        category: ["sn0w", "ContextMenu", "Preview Image Delay"],
        name: "Preview Image Delay (ms)",
        defaultValue: 300,
        type: "slider",
        attrs: { min: 0, max: 500, step: 10 },
    },
];
const favouriteLoraId = "sn0w.FavouriteLoras";

let loraLoaders = ["Load Lora Sn0w", "LoraLoader"];
let existingList = [];

app.registerExtension({
    name: "sn0w.LoraContextMenu",
    init() {
        settingDefinitions.forEach((settingDefinition) => {
            app.ui.settings.addSetting(settingDefinition);
        });
    },
    async setup() {
        const hasSyntaxHighlight = await SettingUtils.fetchApi("/SyntaxHighlighter/enabled");
        if (hasSyntaxHighlight.enabled) {
            SettingUtils.logSn0w("Syntax Highlighter is enabled.", "informational", "lora");
            return;
        }

        const customLoaderKeys = ["sn0w.CustomLoraLoaders", "sn0w.CustomLoraLoaders.XL", "sn0w.CustomLoraLoaders.3"];
        let customLoraLoadersArrays = [];

        // Fetch and process each custom loader
        for (const key of customLoaderKeys) {
            const customLoaders = await SettingUtils.getSetting(key);
            let customLoaderArray = [];
            if (customLoaders) {
                customLoaderArray = customLoaders.split("\n").map((item) => item.split(":")[0]);
            }
            customLoraLoadersArrays.push(customLoaderArray);
        }

        existingList = await SettingUtils.getSetting(favouriteLoraId);

        if (!Array.isArray(existingList)) {
            existingList = [];
        }

        // Combine the existing custom loaders with the fetched ones
        loraLoaders = loraLoaders.concat(...customLoraLoadersArrays);
        addLoraLoaders(loraLoaders);

        const original_getNodeMenuOptions = app.canvas.getNodeMenuOptions;
        app.canvas.getNodeMenuOptions = function (node) {
            const options = original_getNodeMenuOptions.apply(this, arguments);

            // Collect all Lora widgets.
            if (!node.widgets) {
                return options;
            }
            const loraWidgets = node.widgets.filter((widget) => widget.name.includes("lora") && widget.type === "combo");
            const totalLoras = loraWidgets.length;

            if (loraLoaders.includes(node.type)) {
                const settingUtils = new SettingUtils();
                const nullIndex = options.indexOf(null);
                let optionsArr = [];

                loraWidgets.forEach((widget) => {
                    const selectedLora = widget.value;
                    const pathArray = selectedLora.split("\\");
                    const filename = pathArray[pathArray.length - 1];
                    if (filename == "None") {
                        return;
                    }
                    const isFavourite = existingList.includes(filename);

                    const newMenuItem = {
                        content: (isFavourite ? "Unfavourite " : "Favourite ") + filename.split(".")[0] + (isFavourite ? " ☆" : " ★"),
                        disabled: false,
                        callback: () => {
                            SettingUtils.toggleFavourite(existingList, filename, favouriteLoraId);
                            settingUtils.refreshComboInSingleNode(app, node.title);
                        },
                    };

                    const itemExists = optionsArr.some((item) => item.content === newMenuItem.content);

                    if (!itemExists) {
                        optionsArr.push(newMenuItem);
                    }
                });

                let menuItem;
                if (optionsArr.length > 0) {
                    if (totalLoras === 1) {
                        menuItem = optionsArr[0];
                    } else if (totalLoras > 1) {
                        menuItem = {
                            content: "Favourite",
                            disabled: false,
                            has_submenu: true,
                            submenu: {
                                options: optionsArr,
                            },
                        };
                    }
                } else {
                    menuItem = {
                        content: "No lora selected",
                        disabled: true,
                    };
                }

                if (nullIndex !== -1) {
                    options.splice(nullIndex, 0, menuItem);
                } else {
                    options.push(menuItem);
                }
            }
            return options;
        };

        SettingUtils.observeContextMenu(existingList);
    },
});
