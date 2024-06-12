import { SettingUtils } from './sn0w.js';
import { app } from "../../../scripts/app.js";

const defaultValue = "ExampleName1:Value1\nExampleName2:Value2";
const height = "60"
const tooltip = "Enter each name-value pair on a new line, separated by a colon (:)."

const xlId = "sn0w.CustomLoraLoadersXL";
const xlSettingDefinition = {
    id: xlId,
    name: "[Sn0w] Custom Lora Loaders SDXL",
    type: SettingUtils.createMultilineSetting,
    defaultValue: defaultValue,
    attrs: {
        height: height,
        tooltip: tooltip,
    }
};

const nonXlId = "sn0w.CustomLoraLoaders1.5";
const nonXlSettingDefinition = {
    id: nonXlId,
    name: "[Sn0w] Custom Lora Loaders SD 1.5",
    type: SettingUtils.createMultilineSetting,
    defaultValue: defaultValue,
    attrs: {
        height: height,
        tooltip: tooltip,
    }
};

const threeId = "sn0w.CustomLoraLoaders3";
const threeSettingDefinition = {
    id: threeId,
    name: "[Sn0w] Custom Lora Loaders SD3",
    type: SettingUtils.createMultilineSetting,
    defaultValue: defaultValue,
    attrs: {
        height: height,
        tooltip: tooltip,
    }
};

const registerSetting = (settingDefinition) => {
    const extension = {
        name: settingDefinition.id,
        init() {
            const setting = app.ui.settings.addSetting(settingDefinition);
        }
    };
    app.registerExtension(extension);
};

registerSetting(xlSettingDefinition);
registerSetting(nonXlSettingDefinition);
registerSetting(threeSettingDefinition);
