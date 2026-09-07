import { app } from "../../../scripts/app.js";
import { SettingUtils } from "./sn0w.js";

const LOADER_INFO_ROUTE = "/sn0w/lora_loader_info";
const PRESETS_ROUTE = "/sn0w/lora_presets";

let loaderInfo = {};

const suffixForIndex = (index) => String.fromCharCode(97 + index);

const collectPreset = (node, info) => {
    const loras = [];
    for (let i = 0; i < info.combos; i++) {
        const suffix = suffixForIndex(i);
        const loraWidget = node.widgets.find((w) => w.name === `lora_${suffix}`);
        const strengthWidget = node.widgets.find((w) => w.name === `lora_strength_${suffix}`);
        if (!loraWidget) break;
        if (loraWidget.value && loraWidget.value !== "None") {
            loras.push({ lora: loraWidget.value, strength: strengthWidget?.value ?? 1.0 });
        }
    }
    return loras;
};

const savePreset = async (node, info) => {
    const name = window.prompt("Preset name:", "");
    if (!name || !name.trim()) return;
    const trimmedName = name.trim();
    const loras = collectPreset(node, info);
    const result = await SettingUtils.fetchApi(PRESETS_ROUTE, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name: trimmedName, path: info.path, loras }),
    });
    if (result?.status !== "ok") return;

    const settingUtils = new SettingUtils();
    for (const [typeName, typeInfo] of Object.entries(loaderInfo)) {
        if (typeInfo.path === info.path) {
            settingUtils.refreshComboInSingleNode(app, typeName);
        }
    }
};

app.registerExtension({
    name: "sn0w.LoraPresets",
    async setup() {
        loaderInfo = (await SettingUtils.fetchApi(LOADER_INFO_ROUTE)) || {};
    },
    beforeRegisterNodeDef(nodeType) {
        const getExtraMenuOptions = nodeType.prototype.getExtraMenuOptions;
        nodeType.prototype.getExtraMenuOptions = function (_, options) {
            if (getExtraMenuOptions) getExtraMenuOptions.apply(this, arguments);
            const info = loaderInfo[this.type] || loaderInfo[this.comfyClass];
            if (!info) return;

            options.unshift({
                content: "Save Current as Preset",
                callback: () => savePreset(this, info),
            });
        };
    },
});
