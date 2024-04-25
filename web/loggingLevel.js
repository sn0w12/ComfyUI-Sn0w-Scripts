import { app } from "../../../scripts/app.js";

const id = "sn0w.LoggingLevel";
const settingDefinition = {
    id,
    name: "[Sn0w] Logging Level",
    type: "combo",
    defaultValue: "ERRORS_ONLY",
    options: [
        { text: "Errors Only", value: "ERRORS_ONLY" },
        { text: "Warnings and Above", value: "WARNINGS_ABOVE" },
        { text: "Informational and Above", value: "INFO_ABOVE" },
        { text: "All Logs", value: "ALL" }
    ],
};

let setting;

const extension = {
    name: id,
    init() {
        setting = app.ui.settings.addSetting(settingDefinition);
    },
};

app.registerExtension(extension);
