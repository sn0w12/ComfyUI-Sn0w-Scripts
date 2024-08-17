import { app } from '../../../scripts/app.js';

const id = 'sn0w.PromptFormat';
const settingDefinition = {
    id,
    name: 'Animagine Prompt Style',
    defaultValue: false,
    type: 'boolean',
    tooltip: 'Puts 1girl/ 1boy at the front of prompts.',
};

let setting;

const extension = {
    name: id,
    init() {
        setting = app.ui.settings.addSetting(settingDefinition);
    },
};

app.registerExtension(extension);
