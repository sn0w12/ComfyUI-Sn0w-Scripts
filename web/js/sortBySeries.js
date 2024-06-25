import { SettingUtils } from './sn0w.js';
import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

function updateSorting() {
    api.fetchApi(`${SettingUtils.API_PREFIX}/update_characters`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        }
    })
    setTimeout(() => {
        app.refreshComboInNodes();
    }, 50);
}

const id = "sn0w.SortBySeries";
const settingDefinition = {
    id,
    name: "[Sn0w] Sort Characters By Series",
    defaultValue: false,
    type: "boolean",
    onChange: () => updateSorting(),
};

let setting;

const extension = {
    name: id,
    init() {
        setting = app.ui.settings.addSetting(settingDefinition);
    },
};

app.registerExtension(extension);
