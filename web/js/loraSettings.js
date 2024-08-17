import { SettingUtils } from './sn0w.js';
import { app } from '../../../scripts/app.js';
import { api } from '../../../scripts/api.js';

async function fetchExtensionSettings() {
    return SettingUtils.fetchApi("/extensions/ComfyUI-Sn0w-Scripts/settings/sn0w_settings.json");
}
const settingUtils = new SettingUtils();

async function updateLoraSorting(graphCanvas) {
    const tempSn0wSettings = await fetchExtensionSettings();
    setTimeout(() => {
        let loraLoaders = tempSn0wSettings['loraLoaders'];
        if (loraLoaders != undefined) {
            loraLoaders.forEach((loraLoader) => {
                let node = null;
                for (const graphNode of Object.values(graphCanvas.graph._nodes)) {
                    if (graphNode.type === loraLoader) {
                        settingUtils.refreshComboInSingleNode(graphCanvas, loraLoader);
                    }
                }
            })
        }
    }, 50);
}

const defaultValue = 'ExampleName1:Value1\nExampleName2:Value2';
const tooltip = 'Enter each name-value pair on a new line, separated by a colon (:).';

const settingsMap = {
    'sn0w.CustomLoraLoaders': 'loras_15',
    'sn0w.CustomLoraLoaders.XL': 'loras_xl',
    'sn0w.CustomLoraLoaders.3': 'loras_3',
};

const loraLoadersSettingsDefinitions = [
    {
        id: 'sn0w.CustomLoraLoaders',
        name: 'Custom Lora Loaders SD 1.5',
        type: SettingUtils.createMultilineSetting,
        defaultValue: defaultValue,
        attrs: { tooltip: tooltip },
    },
    {
        id: 'sn0w.CustomLoraLoaders.XL',
        name: 'Custom Lora Loaders SDXL',
        type: SettingUtils.createMultilineSetting,
        defaultValue: defaultValue,
        attrs: { tooltip: tooltip },
    },
    {
        id: 'sn0w.CustomLoraLoaders.3',
        name: 'Custom Lora Loaders SD3',
        type: SettingUtils.createMultilineSetting,
        defaultValue: defaultValue,
        attrs: { tooltip: tooltip },
    },
];

const loraSettingsDefinitions = [
    {
        id: 'sn0w.LoraSettings.SortLorasBy',
        name: 'Sort Loras By',
        defaultValue: "alphabetical",
        options: [
            { text: 'Alphabetical', value: 'alphabetical' },
            { text: 'Last Changed', value: 'last_changed' },
        ],
        type: 'combo',
        onChange: () => updateLoraSorting(app),
    },
    {
        id: 'sn0w.LoraSettings.RemoveLoraPath',
        name: 'Remove Lora Path',
        defaultValue: false,
        type: 'boolean',
        onChange: () => updateLoraSorting(app),
    },
    {
        id: 'sn0w.LoraSettings.LoraFolderMinDistance',
        name: 'Max difference in Lora Loading',
        defaultValue: 5,
        min: 0,
        max: 20,
        step: 1,
        type: 'slider',
    }
]

const registerSetting = (settingDefinition) => {
    const extension = {
        name: settingDefinition.id,
        init() {
            const setting = app.ui.settings.addSetting({
                id: settingDefinition.id,
                name: settingDefinition.name,
                type: settingDefinition.type,
                defaultValue: settingDefinition.defaultValue,
                attrs: settingDefinition.attrs,
                options: settingDefinition.options,
                onChange: settingDefinition.onChange,
            });
        },
    };
    app.registerExtension(extension);
};

const sn0wSettings = await fetchExtensionSettings();
// Register settings
loraLoadersSettingsDefinitions.forEach((setting) => {
    if (sn0wSettings['loaders_enabled'].includes(settingsMap[setting.id])) {
        registerSetting(setting);
    }
});

loraSettingsDefinitions.forEach((setting) => {
    registerSetting(setting);
});
