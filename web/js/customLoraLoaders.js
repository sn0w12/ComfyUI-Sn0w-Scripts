import { SettingUtils } from './sn0w.js';
import { app } from "../../../scripts/app.js";

const defaultValue = "ExampleName1:Value1\nExampleName2:Value2";
const tooltip = "Enter each name-value pair on a new line, separated by a colon (:).";

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
settingsDefinitions.forEach(registerSetting);
