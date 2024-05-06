export class SettingUtils {
    static API_PREFIX = '/sn0w';

    static createMultilineSetting(name, setter, value, attrs) {
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

    static createCheckboxSetting(name, setter, value, attrs) {
        const tr = document.createElement("tr");
        const tdLabel = document.createElement("td");
        const tdInput = document.createElement("td");
        const label = document.createElement("label");
    
        // Generate a unique ID for the setting container
        const uniqueId = `custom-setting-${Date.now()}`;
        label.setAttribute("for", uniqueId);
        label.textContent = name;
    
        // Checkbox container
        const checkboxContainer = document.createElement("div");
        checkboxContainer.id = uniqueId;
        checkboxContainer.style.padding = "5px";
        checkboxContainer.style.display = "block";  // Ensure it is initially visible
    
        // Hide button
        const hideButton = document.createElement("button");
        hideButton.textContent = "Show";
        checkboxContainer.style.display = "none";
        hideButton.onclick = () => {
            checkboxContainer.style.display = checkboxContainer.style.display === "none" ? "block" : "none";
            hideButton.textContent = checkboxContainer.style.display === "none" ? "Show" : "Hide";
            hideButton.style.marginBottom = checkboxContainer.style.display === "none" ? "0px" : "5px";
        };
        hideButton.style.width = "100%"
    
        // Append the hide button before the checkboxes
        tdInput.appendChild(hideButton);
    
        // Initialize values array based on the default value
        let values = Array.isArray(value) ? value : [value];
    
        // Create checkboxes based on the options provided in attrs
        attrs.options.forEach(option => {
            const checkbox = document.createElement("input");
            const checkboxLabel = document.createElement("label");
            const checkboxId = `${uniqueId}-${option.value}`;
    
            checkbox.type = "checkbox";
            checkbox.id = checkboxId;
            checkbox.checked = values.includes(option.value);
            checkbox.onchange = () => {
                if (checkbox.checked && !values.includes(option.value)) {
                    values.push(option.value);
                } else if (!checkbox.checked && values.includes(option.value)) {
                    values = values.filter(v => v !== option.value);
                }
                setter(values); // Update the setting with the current array of selected values
            };
    
            checkboxLabel.setAttribute("for", checkboxId);
            checkboxLabel.textContent = option.label;
            checkboxLabel.style.marginRight = "10px";
    
            const wrapper = document.createElement("div");
            wrapper.appendChild(checkbox);
            wrapper.appendChild(checkboxLabel);
            checkboxContainer.appendChild(wrapper);
        });
    
        tdInput.appendChild(checkboxContainer);
    
        tdLabel.appendChild(label);
        tr.appendChild(tdLabel);
        tr.appendChild(tdInput);
    
        const tooltip = attrs.tooltip;
    
        // Set tooltip if provided
        if (tooltip) {
            tr.title = tooltip;
            label.className = "comfy-tooltip-indicator";
        }
    
        return tr;
    }

    static debounce(func, delay) {
        let debounceTimer;
        return function() {
            const context = this;
            const args = arguments;
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => func.apply(context, args), delay);
        };
    }
}
