import { app } from "../../../scripts/app.js";

function createMultilineTextSetting(name, setter, value, attrs, tooltip = "") {
    // Create elements
    const tr = document.createElement("tr");
    const tdLabel = document.createElement("td");
    const tdInput = document.createElement("td");
    const label = document.createElement("label");
    const textarea = document.createElement("textarea");

    // Configure label
    const uniqueId = `custom-setting-${Date.now()}`; // Unique ID for associating label with textarea
    label.setAttribute("for", uniqueId);
    label.textContent = name;
    label.className = "comfy-tooltip-indicator";

    // Configure textarea
    textarea.id = uniqueId;
    textarea.value = value;
    textarea.setAttribute("style", "width: 100%; height: 100px; resize: none;"); // Fixed size and non-resizable

    // Set event handlers
    textarea.onchange = () => {
        setter(textarea.value);
    };

    // Set additional attributes
    for (const [key, val] of Object.entries(attrs)) {
        textarea.setAttribute(key, val);
    }

    // Append elements to the document
    tdLabel.appendChild(label);
    tdInput.appendChild(textarea);
    tr.appendChild(tdLabel);
    tr.appendChild(tdInput);

    // Set tooltip if available
    if (tooltip) {
        label.title = tooltip; // Set the tooltip text
    }

    return tr;
}

// Define settings for "Custom Lora Loaders XL"
const xlId = "sn0w.CustomLoraLoadersXL";
const xlSettingDefinition = {
    id: xlId,
    name: "[Sn0w] Custom Lora Loaders XL",
    type: createMultilineTextSetting,
    defaultValue: "ExampleName1:Value1\nExampleName2:Value2",
    tooltip: "Enter each name-value pair on a new line, separated by a colon (:)."
};

// Define settings for "Custom Lora Loaders" (without XL)
const nonXlId = "sn0w.CustomLoraLoaders1.5";
const nonXlSettingDefinition = {
    id: nonXlId,
    name: "[Sn0w] Custom Lora Loaders 1.5",
    type: createMultilineTextSetting,
    defaultValue: "ExampleName1:Value1\nExampleName2:Value2",
    tooltip: "Enter each name-value pair on a new line, separated by a colon (:)."
};

// Register extensions for both settings
const registerSetting = (settingDefinition) => {
    const extension = {
        name: settingDefinition.id,
        init() {
            const setting = app.ui.settings.addSetting(settingDefinition);
        }
    };
    app.registerExtension(extension);
};

registerSetting(xlSettingDefinition);
registerSetting(nonXlSettingDefinition);
