import { SettingUtils } from './sn0w.js';
import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

async function fetchExtensionSettings() {
    try {
        const response = await api.fetchApi('/extensions/ComfyUI-Sn0w-Scripts/settings/sn0w_settings.json');
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
const defaultValue = "ExampleName1:Value1\nExampleName2:Value2";
const tooltip = "Enter each name-value pair on a new line, separated by a colon (:).";

const settingsMap = {
    "sn0w.CustomLoraLoaders1.5": "loras_15",
    "sn0w.CustomLoraLoadersXL": "loras_xl",
    "sn0w.CustomLoraLoaders3": "loras_3"
}

const settingsDefinitions = [
    {
        id: "sn0w.CustomLoraLoadersXL",
        name: "[Sn0w] Custom Lora Loaders SDXL",
        defaultValue: defaultValue,
        attrs: { tooltip: tooltip }
    },
    {
        id: "sn0w.CustomLoraLoaders1.5",
        name: "[Sn0w] Custom Lora Loaders SD 1.5",
        defaultValue: defaultValue,
        attrs: { tooltip: tooltip }
    },
    {
        id: "sn0w.CustomLoraLoaders3",
        name: "[Sn0w] Custom Lora Loaders SD3",
        defaultValue: defaultValue,
        attrs: { tooltip: tooltip }
    }
];

const registerSetting = (settingDefinition) => {
    const extension = {
        name: settingDefinition.id,
        init() {
            const setting = app.ui.settings.addSetting({
                id: settingDefinition.id,
                name: settingDefinition.name,
                type: SettingUtils.createMultilineSetting,
                defaultValue: settingDefinition.defaultValue,
                attrs: settingDefinition.attrs
            });
        }
    };
    app.registerExtension(extension);
};

// Register settings
settingsDefinitions.forEach(setting => {
    if (sn0wSettings["loaders_enabled"].includes(settingsMap[setting.id])) {
        registerSetting(setting);
    }
});
