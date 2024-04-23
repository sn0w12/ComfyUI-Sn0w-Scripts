import { app } from "../../../scripts/app.js";

const id = "sn0w.LoggingLevel";
const settingDefinition = {
    id,
    name: "[Sn0w] Logging Level",
    type: "combo",
    defaultValue: "NONE",
    options: [
        { text: "None", value: "NONE" },
        { text: "General", value: "GENERAL" },
        { text: "All", value: "ALL" }
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
