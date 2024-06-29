import { SettingUtils } from './sn0w.js';
import { app } from '../../../scripts/app.js';

const id = 'sn0w.HighlightFavourite';
const settingDefinition = {
    id,
    name: '[Sn0w] Highlight Favourite Items',
    defaultValue: false,
    type: 'boolean',
};
const favouriteLoraId = 'sn0w.FavouriteLoras';

let loraLoaders = ['Load Lora Sn0w', 'LoraLoader'];
let existingList = [];

app.registerExtension({
    name: 'sn0w.LoraContextMenu',
    init() {
        let setting = app.ui.settings.addSetting(settingDefinition);
    },
    async setup() {
        const customLoaderKeys = [
            'sn0w.CustomLoraLoadersXL',
            'sn0w.CustomLoraLoaders15',
            'sn0w.CustomLoraLoaders3',
        ];
        let customLoraLoadersArrays = [];

        // Fetch and process each custom loader
        for (const key of customLoaderKeys) {
            const customLoaders = await SettingUtils.getSetting(key);
            let customLoaderArray = [];
            if (customLoaders) {
                customLoaderArray = customLoaders.split('\n').map((item) => item.split(':')[0]);
            }
            customLoraLoadersArrays.push(customLoaderArray);
        }

        existingList = await SettingUtils.getSetting(favouriteLoraId);

        if (!Array.isArray(existingList)) {
            existingList = [];
        }

        // Combine the existing custom loaders with the fetched ones
        loraLoaders = loraLoaders.concat(...customLoraLoadersArrays);

        const original_getNodeMenuOptions = app.canvas.getNodeMenuOptions;
        app.canvas.getNodeMenuOptions = function (node) {
            const options = original_getNodeMenuOptions.apply(this, arguments);
            if (loraLoaders.includes(node.type)) {
                const settingUtils = new SettingUtils();
                const nullIndex = options.indexOf(null);

                // Check if the filename is in the existingList
                const selectedLora = node.widgets[0].value;
                const pathArray = selectedLora.split('\\');
                const filename = pathArray[pathArray.length - 1];
                const isFavourite = existingList.includes(filename);

                // Create the new menu item
                const newMenuItem = {
                    content: isFavourite ? 'Unfavourite Lora ☆' : 'Favourite Lora ★',
                    disabled: false,
                    callback: () => {
                        SettingUtils.toggleFavourite(existingList, filename, favouriteLoraId);
                        settingUtils.refreshComboInSingleNode(app, node.title);
                    },
                };

                if (nullIndex !== -1) {
                    options.splice(nullIndex, 0, newMenuItem);
                } else {
                    options.push(newMenuItem);
                }
            }
            return options;
        };

        var observer = new MutationObserver(function (mutations) {
            if (document.contains(document.getElementsByClassName('litecontextmenu')[0])) {
                SettingUtils.addStarsToFavourited(existingList);
            }
        });

        observer.observe(document, {
            attributes: false,
            childList: true,
            characterData: false,
            subtree: true,
        });
    },
});
