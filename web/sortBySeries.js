import { app } from "../../../scripts/app.js";

const id = "sn0w.SortBySeries";
const settingDefinition = {
    id,
    name: "[Sn0w] Sort Characters By Series",
    defaultValue: false,
    type: "boolean",
};

let setting;

const extension = {
    name: id,
    init() {
        setting = app.ui.settings.addSetting(settingDefinition);
    },
};

app.registerExtension(extension);
