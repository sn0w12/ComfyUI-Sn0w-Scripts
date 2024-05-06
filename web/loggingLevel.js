import { SettingUtils } from './sn0w.js';
import { app } from "../../../scripts/app.js";
import { api } from '../../scripts/api.js';

function updateLoggingLevel() {
    api.fetchApi(`${SettingUtils.API_PREFIX}/update_sorting`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ update: true }),
    });
}

const debouncedUpdateLoggingLevel = SettingUtils.debounce(updateLoggingLevel, 1000);

const id = "sn0w.LoggingLevel";
const settingDefinition = {
    id,
    name: "[Sn0w] Logging Level",
    type: SettingUtils.createCheckboxSetting,
    defaultValue: ["WARNING", "INFORMATIONAL"],
    onChange: debouncedUpdateLoggingLevel,
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
