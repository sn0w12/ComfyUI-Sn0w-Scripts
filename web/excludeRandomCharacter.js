import { SettingUtils } from './sn0w.js';
import { app } from "../../../scripts/app.js";

const Id = "sn0w.ExcludedRandomCharacters";
const SettingDefinition = {
    id: Id,
    name: "[Sn0w] Exclude/Include Random Characters",
    type: SettingUtils.createMultilineSetting,
    defaultValue: "ExampleName1,ExampleName2",
    attrs: {
        height: "50",
        tooltip: "Specify excluded characters as a comma-separated list; prepend 'only:' to include only listed names.",
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

registerSetting(SettingDefinition);
