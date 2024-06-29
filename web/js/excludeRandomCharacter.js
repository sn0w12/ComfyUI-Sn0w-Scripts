import { app } from '../../../scripts/app.js';

const id = 'sn0w.ExcludedRandomCharacters';
const settingDefinition = {
    id,
    name: '[Sn0w] Random Characters from Favourites Only',
    defaultValue: false,
    type: 'boolean',
};

let setting;

const extension = {
    name: id,
    init() {
        setting = app.ui.settings.addSetting(settingDefinition);
    },
};

app.registerExtension(extension);
