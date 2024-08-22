import { SettingUtils } from './sn0w.js';
import { app } from '../../../scripts/app.js';

const favouriteCharactersId = 'sn0w.FavouriteCharacters';
let existingList = [];

app.registerExtension({
    name: 'sn0w.CharacterContextMenu',
    async setup() {
        existingList = await SettingUtils.getSetting('sn0w.FavouriteCharacters');
        if (!Array.isArray(existingList)) {
            existingList = [];
        }

        const original_getNodeMenuOptions = app.canvas.getNodeMenuOptions;
        app.canvas.getNodeMenuOptions = function (node) {
            const options = original_getNodeMenuOptions.apply(this, arguments);
            if (node.type === 'Character Selector') {
                const settingUtils = new SettingUtils();
                const nullIndex = options.indexOf(null);

                // Check if the filename is in the existingList
                const selectedCharacter = node.widgets[0].value;
                const isFavourite = existingList.includes(selectedCharacter);

                // Create the new menu item
                const newMenuItem = {
                    content: isFavourite ? 'Unfavourite Character ☆' : 'Favourite Character ★',
                    disabled: false,
                    callback: () => {
                        SettingUtils.toggleFavourite(
                            existingList,
                            selectedCharacter,
                            favouriteCharactersId
                        );
                        settingUtils.refreshComboInSingleNode(app, 'Character Selector');
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

        SettingUtils.observeContextMenu(existingList);
    },
});
