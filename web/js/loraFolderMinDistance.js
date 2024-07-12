import { app } from '../../../scripts/app.js';

const id = 'sn0w.LoraFolderMinDistance';
const settingDefinition = {
    id,
    name: '[Sn0w] Max difference in Lora Loading',
    defaultValue: 5,
    min: 0,
    max: 20,
    step: 1,
    type: 'slider',
};

let setting;

const extension = {
    name: id,
    init() {
        setting = app.ui.settings.addSetting(settingDefinition);
    },
};

app.registerExtension(extension);
