import { SettingUtils } from './sn0w.js';
import { app } from '../../../scripts/app.js';
import { api } from '../../../scripts/api.js';

const settingUtils = new SettingUtils();

function updateSorting(graphCanvas) {
    api.fetchApi(`${SettingUtils.API_PREFIX}/update_characters`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    });
    setTimeout(() => {
        settingUtils.refreshComboInSingleNode(graphCanvas, 'Character Selector');
    }, 50);
}

const id = 'sn0w.CharacterSettings.SortCharactersBy';
const settingDefinition = {
    id,
    name: 'Sort Characters By',
    defaultValue: 'alphabetical',
    options: [
        { text: 'Alphabetical', value: 'alphabetical' },
        { text: 'Series', value: 'series' },
    ],
    type: 'combo',
    onChange: () => updateSorting(app),
};

let setting;

const extension = {
    name: id,
    init() {
        setting = app.ui.settings.addSetting(settingDefinition);
    },
};

app.registerExtension(extension);
