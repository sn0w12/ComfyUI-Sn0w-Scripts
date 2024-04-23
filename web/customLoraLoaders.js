import { app } from "../../../scripts/app.js";

function createMultilineTextSetting(name, setter, value, attrs, tooltip = "") {
    console.log("Tooltip received:", tooltip); // Debug to check tooltip value

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

    // Check for tooltip and apply the class and title
    if (tooltip) {
        label.className = "comfy-tooltip-indicator"; // Apply tooltip indicator class
        console.log("Class set:", label.className); // Debug to verify class set
    }

    // Configure textarea
    textarea.id = uniqueId;
    textarea.value = value;
    textarea.style.width = "100%";
    textarea.style.height = "100px";
    textarea.style.resize = "none";

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

    return tr;
}

// Define a wrapper function for creating the multiline text setting that includes the tooltip
const createMultilineTextSettingWithTooltip = (name, defaultValue, tooltip) => {
    return () => createMultilineTextSetting(name, value => console.log(`Setting ${name} updated to: ${value}`), defaultValue, {}, tooltip);
};

// Define settings for "Custom Lora Loaders XL"
const xlSettingDefinition = {
    id: "sn0w.CustomLoraLoadersXL",
    name: "[Sn0w] Custom Lora Loaders XL",
    type: createMultilineTextSettingWithTooltip(
        "[Sn0w] Custom Lora Loaders XL",
        "ExampleName1:Value1\nExampleName2:Value2",
        "Enter each name-value pair on a new line, separated by a colon (:)."
    ),
    defaultValue: "ExampleName1:Value1\nExampleName2:Value2",
    tooltip: "Enter each name-value pair on a new line, separated by a colon (:)."
};

// Define settings for "Custom Lora Loaders" (without XL)
const nonXlSettingDefinition = {
    id: "sn0w.CustomLoraLoaders1.5",
    name: "[Sn0w] Custom Lora Loaders 1.5",
    type: createMultilineTextSettingWithTooltip(
        "[Sn0w] Custom Lora Loaders 1.5",
        "ExampleName1:Value1\nExampleName2:Value2",
        "Enter each name-value pair on a new line, separated by a colon (:)."
    ),
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
