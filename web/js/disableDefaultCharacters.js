import { SettingUtils } from './sn0w.js';
import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const settingUtils = new SettingUtils()

function updateSorting(graphCanvas) {
    api.fetchApi(`${SettingUtils.API_PREFIX}/update_characters`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        }
    })
    setTimeout(() => {
        settingUtils.refreshComboInSingleNode(graphCanvas, "Character Selector");
    }, 50);
}

const id = "sn0w.DisableDefaultCharacters";
const settingDefinition = {
    id,
    name: "[Sn0w] Disable Default Characters",
    defaultValue: false,
    type: "boolean",
    onChange: () => updateSorting(app),
};

let setting;

const extension = {
    name: id,
    init() {
        setting = app.ui.settings.addSetting(settingDefinition);
    },
};

app.registerExtension(extension);
