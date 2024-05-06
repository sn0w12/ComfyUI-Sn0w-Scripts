import { SettingUtils } from './sn0w.js';
import { app } from "../../../scripts/app.js";

const id = "sn0w.LoggingLevel";
const settingDefinition = {
    id,
    name: "[Sn0w] Logging Level",
    type: SettingUtils.createCheckboxSetting,
    defaultValue: ["WARNING", "INFORMATIONAL"],
    attrs: {
        options: [
            { label: "Warnings", value: "WARNING" },
            { label: "Informational", value: "INFORMATIONAL" },
            { label: "Debug", value: "DEBUG" },
        ],
        tooltip: ""
    }
};

let setting;

const extension = {
    name: id,
    init() {
        setting = app.ui.settings.addSetting(settingDefinition);
    },
};

app.registerExtension(extension);
