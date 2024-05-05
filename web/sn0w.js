export class SettingUtils {
    static createMultilineSetting(name, setter, value, attrs) {
        console.log(attrs)

        const tr = document.createElement("tr");
        const tdLabel = document.createElement("td");
        const tdInput = document.createElement("td");
        const label = document.createElement("label");
        const textarea = document.createElement("textarea");
    
        // Generate a unique ID for associating the label with the textarea
        const uniqueId = `custom-setting-${Date.now()}`;
        label.setAttribute("for", uniqueId);
        label.textContent = name;
    
        textarea.id = uniqueId;
        textarea.value = value;
        textarea.setAttribute("style", `width: 100%; height: ${attrs["height"]}px; resize: none;`);
    
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

        const tooltip = attrs["tooltip"];
    
        // Setting tooltip if provided
        if (tooltip != "") {
            tr.title = tooltip;  
            label.className = "comfy-tooltip-indicator";
        }
    
        return tr;
    }
}
