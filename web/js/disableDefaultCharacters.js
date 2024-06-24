import { app } from "../../../scripts/app.js";

const id = "sn0w.DisableDefaultCharacters";
const settingDefinition = {
    id,
    name: "[Sn0w] Disable Default Characters",
    defaultValue: false,
    type: "boolean"
};

let setting;

const extension = {
    name: id,
    init() {
        setting = app.ui.settings.addSetting(settingDefinition);
    },
};

app.registerExtension(extension);
