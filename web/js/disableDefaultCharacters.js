import { SettingUtils } from './sn0w.js';
import { app } from '../../../scripts/app.js';

const settingUtils = new SettingUtils();

function updateSorting(graphCanvas) {
    setTimeout(() => {
        settingUtils.refreshComboInSingleNode(graphCanvas, 'Character Selector');
    }, 50);
}

const id = 'sn0w.CharacterSettings.DisableDefaultCharacters';
const settingDefinition = {
    id,
    name: 'Disable Default Characters',
    defaultValue: false,
    type: 'boolean',
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
