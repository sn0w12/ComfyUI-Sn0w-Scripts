import { SettingUtils } from './sn0w.js';
import { app } from "../../../scripts/app.js";

const id = "sn0w.HighlightFavourite";
const settingDefinition = {
    id,
    name: "[Sn0w] Highlight Favourite Items",
    defaultValue: false,
    type: "boolean",
};
const favouriteLoraId = "sn0w.FavouriteLoras"

let loraLoaders = ["Load Lora XL", "Load Lora 1.5", "LoraLoader"];
let existingList = [];

app.registerExtension({
    name: "sn0w.LoraContextMenu",
    init() {
        let setting = app.ui.settings.addSetting(settingDefinition);
    },
    async setup() {
        const customLoraLoadersXL = await SettingUtils.getSetting("sn0w.CustomLoraLoadersXL");
        const customLoraLoaders15 = await SettingUtils.getSetting("sn0w.CustomLoraLoaders15");
        existingList = await SettingUtils.getSetting(favouriteLoraId);

        if (!Array.isArray(existingList)) {
            existingList = [];
        }

        let customLoraLoadersXLArray = [];
        if (customLoraLoadersXL) {
            customLoraLoadersXLArray = customLoraLoadersXL.split('\n').map(item => item.split(':')[0]);
        }

        let customLoraLoaders15Array = [];
        if (customLoraLoaders15) {
            customLoraLoaders15Array = customLoraLoaders15.split('\n').map(item => item.split(':')[0]);
        }

        // Combine the existing custom loaders with the fetched ones
        loraLoaders = loraLoaders.concat(customLoraLoadersXLArray, customLoraLoaders15Array);

        const original_getNodeMenuOptions = app.canvas.getNodeMenuOptions;
        app.canvas.getNodeMenuOptions = function (node) {
            const options = original_getNodeMenuOptions.apply(this, arguments);
            if (loraLoaders.includes(node.type)) {
                const nullIndex = options.indexOf(null);
                
                // Check if the filename is in the existingList
                const selectedLora = node.widgets[0].value;
                const pathArray = selectedLora.split('\\');
                const filename = pathArray[pathArray.length - 1];
                const isFavourite = existingList.includes(filename);

                // Create the new menu item
                const newMenuItem = {
                    content: isFavourite ? "Unfavourite Lora ☆" : "Favourite Lora ★",
                    disabled: false,
                    callback: () => {
                        SettingUtils.toggleFavourite(existingList, filename, favouriteLoraId);
                        app.refreshComboInNodes();
                    }
                };

                if (nullIndex !== -1) {
                    options.splice(nullIndex, 0, newMenuItem);
                } else {
                    options.push(newMenuItem);
                }
            }
            return options;
        };

        var observer = new MutationObserver(function(mutations) {
            if (document.contains(document.getElementsByClassName("litecontextmenu")[0])) {
                SettingUtils.addStarsToFavourited(existingList);
            }
        });
         
        observer.observe(document, {attributes: false, childList: true, characterData: false, subtree:true});
    }
});
