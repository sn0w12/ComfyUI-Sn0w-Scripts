import { SettingUtils } from './sn0w.js';
import { app } from '../../../scripts/app.js';
import { api } from '../../../scripts/api.js';

async function fetchExtensionSettings() {
    try {
        const response = await api.fetchApi(
            '/extensions/ComfyUI-Sn0w-Scripts/settings/sn0w_settings.json'
        );
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('There was a problem with the fetch operation:', error);
    }
}

const sn0wSettings = await fetchExtensionSettings();
const settingUtils = new SettingUtils();

// KEPT IN FOR FUTURE INTEGRATION (MAYBE)
function updateLoraSorting(graphCanvas) {
    setTimeout(() => {
        let loraLoaders = sn0wSettings['loraLoaders'];
        loraLoaders.forEach((loraLoader) => {
            let node = null;
            for (const graphNode of Object.values(graphCanvas.graph._nodes)) {
                if (graphNode.type === loraLoader) {
                    node = graphNode;
                    break;
                }
            }
            if (node) {
                settingUtils.refreshComboInSingleNode(graphCanvas, loraLoader);
            }
        })
    }, 50);
}

const defaultValue = 'ExampleName1:Value1\nExampleName2:Value2';
const tooltip = 'Enter each name-value pair on a new line, separated by a colon (:).';

const settingsMap = {
    'sn0w.CustomLoraLoaders1.5': 'loras_15',
    'sn0w.CustomLoraLoadersXL': 'loras_xl',
    'sn0w.CustomLoraLoaders3': 'loras_3',
};

const loraLoadersSettingsDefinitions = [
    {
        id: 'sn0w.CustomLoraLoadersXL',
        name: '[Sn0w] Custom Lora Loaders SDXL',
        type: SettingUtils.createMultilineSetting,
        defaultValue: defaultValue,
        attrs: { tooltip: tooltip },
    },
    {
        id: 'sn0w.CustomLoraLoaders1.5',
        name: '[Sn0w] Custom Lora Loaders SD 1.5',
        type: SettingUtils.createMultilineSetting,
        defaultValue: defaultValue,
        attrs: { tooltip: tooltip },
    },
    {
        id: 'sn0w.CustomLoraLoaders3',
        name: '[Sn0w] Custom Lora Loaders SD3',
        type: SettingUtils.createMultilineSetting,
        defaultValue: defaultValue,
        attrs: { tooltip: tooltip },
    },
];

const loraSettingsDefinitions = [
    {
        id: 'sn0w.SortLorasBy',
        name: '[Sn0w] Sort Loras By',
        defaultValue: defaultValue,
        options: [
            { text: 'Alphabetical', value: 'alphabetical' },
            { text: 'Last Changed', value: 'last_changed' },
        ],
        type: 'combo',
    },
    {
        id: 'sn0w.RemoveLoraPath',
        name: '[Sn0w] Remove Lora Path',
        defaultValue: false,
        type: 'boolean',
    },
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

// Register settings
loraLoadersSettingsDefinitions.forEach((setting) => {
    if (sn0wSettings['loaders_enabled'].includes(settingsMap[setting.id])) {
        registerSetting(setting);
    }
});

loraSettingsDefinitions.forEach((setting) => {
    registerSetting(setting);
});
