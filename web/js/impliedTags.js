import { SettingUtils } from "./sn0w.js";
import { app } from "../../../scripts/app.js";

const id = "sn0w.ImpliedTags";
const settingDefinition = {
    id,
    name: "Implied Tags",
    defaultValue: "",
    type: SettingUtils.createMultilineSetting,
    tooltip: "Enter implied tags, as `tag:implied_tag` on each line. Tags are added by the Prompt Combine node.",
};

let setting;

const extension = {
    name: id,
    init() {
        setting = app.ui.settings.addSetting(settingDefinition);
    },
};

app.registerExtension(extension);
