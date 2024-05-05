export class SettingUtils {
    static createMultilineSetting(name, setter, value, attrs, tooltip = "") {
        const tr = document.createElement("tr");
        const tdLabel = document.createElement("td");
        const tdInput = document.createElement("td");
        const label = document.createElement("label");
        const textarea = document.createElement("textarea");

        // Generate a unique ID for associating the label with the textarea
        const uniqueId = `custom-setting-${Date.now()}`;
        label.setAttribute("for", uniqueId);
        label.textContent = name;
        label.className = "comfy-tooltip-indicator";

        textarea.id = uniqueId;
        textarea.value = value;
        textarea.setAttribute("style", "width: 100%; height: 100px; resize: none;");

        // Apply event handler
        textarea.onchange = () => setter(textarea.value);

        // Apply additional attributes
        for (const [key, val] of Object.entries(attrs)) {
            textarea.setAttribute(key, val);
        }

        tdLabel.appendChild(label);
        tdInput.appendChild(textarea);
        tr.appendChild(tdLabel);
        tr.appendChild(tdInput);

        if (tooltip) {
            label.title = tooltip;  // Setting tooltip if provided
        }

        return tr;
    }
}
