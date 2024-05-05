import { SettingUtils } from './sn0w.js';
import { app } from "../../../scripts/app.js";

const xlId = "sn0w.CustomLoraLoadersXL";
const xlSettingDefinition = {
    id: xlId,
    name: "[Sn0w] Custom Lora Loaders XL",
    type: SettingUtils.createMultilineSetting,
    defaultValue: "ExampleName1:Value1\nExampleName2:Value2",
    attrs: {
        height: "80",
        tooltip: "Enter each name-value pair on a new line, separated by a colon (:).",
    }
};

const nonXlId = "sn0w.CustomLoraLoaders1.5";
const nonXlSettingDefinition = {
    id: nonXlId,
    name: "[Sn0w] Custom Lora Loaders 1.5",
    type: SettingUtils.createMultilineSetting,
    defaultValue: "ExampleName1:Value1\nExampleName2:Value2",
    attrs: {
        height: "80",
        tooltip: "Enter each name-value pair on a new line, separated by a colon (:).",
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
