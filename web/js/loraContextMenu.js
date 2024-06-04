import { SettingUtils } from './sn0w.js';
import { app } from "../../../scripts/app.js";
import { api } from '../../../scripts/api.js';

let customLoraLoaders = ["Load Lora XL", "Load Lora 1.5"];
let existingList = [];

// Callback function to add or remove the filename from the settings list
async function toggleFavouriteLora(filename) {
    try {
        // Check if the filename is already in the list
        const index = existingList.indexOf(filename);
        if (index === -1) {
            // Add the new filename to the list
            existingList.push(filename);
        } else {
            // Remove the filename from the list
            existingList.splice(index, 1);
        }

        // Store the updated list back in the settings
        await api.storeSetting('sn0w.FavouriteLoras', existingList);
    } catch (error) {
        console.error('Error updating settings:', error);
    }
}

async function addStarsToFavouritedLoras() {
    const menuEntries = document.querySelectorAll('.litemenu-entry');
    const highlightLora = await SettingUtils.getSetting("sn0w.HighlightLoras");

    menuEntries.forEach(entry => {
        const value = entry.getAttribute('data-value');
        let filename = value;
        if (value !== null && value.includes('\\')) {
            const pathArray = value.split('\\');
            filename = pathArray[pathArray.length - 1];
        }
        
        if (existingList.includes(filename)) {
            // Create star element
            const star = document.createElement('span');
            star.innerHTML = '★';
            star.style.cssFloat = 'right'; // Align star to the right

            // Check if star is already added to avoid duplication
            if (!entry.querySelector('span')) {
                entry.appendChild(star);
            }
            if (highlightLora) {
                entry.setAttribute( 'style', 'background-color: green !important' );
            }
        }
    });
}

const id = "sn0w.HighlightLoras";
const settingDefinition = {
    id,
    name: "[Sn0w] Highlight Favourite Loras",
    defaultValue: false,
    type: "boolean",
};

app.registerExtension({
    name: id,
    init() {
        setting = app.ui.settings.addSetting(settingDefinition);
    },
    async setup() {
        const customLoraLoadersXL = await SettingUtils.getSetting("sn0w.CustomLoraLoadersXL");
        const customLoraLoaders15 = await SettingUtils.getSetting("sn0w.CustomLoraLoaders15");
        existingList = await SettingUtils.getSetting("sn0w.FavouriteLoras");

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
        customLoraLoaders = customLoraLoaders.concat(customLoraLoadersXLArray, customLoraLoaders15Array);

        const original_getNodeMenuOptions = app.canvas.getNodeMenuOptions;
        app.canvas.getNodeMenuOptions = function (node) {
            const options = original_getNodeMenuOptions.apply(this, arguments);
            if (customLoraLoaders.includes(node.type)) {
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
                        toggleFavouriteLora(filename);
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
                addStarsToFavouritedLoras();
            }
        });
         
        observer.observe(document, {attributes: false, childList: true, characterData: false, subtree:true});
    }
});
