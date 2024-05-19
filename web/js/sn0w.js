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
        checkboxContainer.style.display = "block"; // Ensure it is initially visible
    
        // Hide button
        const hideButton = document.createElement("button");
        hideButton.textContent = "Show";
        checkboxContainer.style.display = "none";
        hideButton.onclick = () => {
            checkboxContainer.style.display = checkboxContainer.style.display === "none" ? "block" : "none";
            hideButton.textContent = checkboxContainer.style.display === "none" ? "Show" : "Hide";
            hideButton.style.marginBottom = checkboxContainer.style.display === "none" ? "0px" : "5px";
        };
        hideButton.style.width = "100%";
    
        // Append the hide button before the checkboxes
        tdInput.appendChild(hideButton);
    
        // Initialize values array based on the default value
        let values = Array.isArray(value) ? value : [value];
    
        // Define the threshold for showing the "Check All" checkbox
        const threshold = 10;
    
        // Check if the number of options exceeds the threshold
        if (attrs.options.length > threshold) {
            // Create "Check All" checkbox
            const checkAllContainer = document.createElement("div");
            const checkAllCheckbox = document.createElement("input");
            const checkAllLabel = document.createElement("label");
            const checkAllId = `${uniqueId}-check-all`;
    
            checkAllCheckbox.type = "checkbox";
            checkAllCheckbox.id = checkAllId;
            checkAllCheckbox.onchange = () => {
                const allCheckboxes = checkboxContainer.querySelectorAll('input[type="checkbox"]');
                allCheckboxes.forEach(checkbox => {
                    checkbox.checked = checkAllCheckbox.checked;
                    const optionValue = checkbox.id.split('-').pop();
                    if (checkAllCheckbox.checked && !values.includes(optionValue)) {
                        values.push(optionValue);
                    } else if (!checkAllCheckbox.checked && values.includes(optionValue)) {
                        values = values.filter(v => v !== optionValue);
                    }
                });
                setter(values); // Update the setting with the current array of selected values
            };
    
            checkAllLabel.setAttribute("for", checkAllId);
            checkAllLabel.textContent = "Check All";
            checkAllLabel.style.marginRight = "10px";
    
            checkAllContainer.appendChild(checkAllCheckbox);
            checkAllContainer.appendChild(checkAllLabel);
            checkboxContainer.appendChild(checkAllContainer);
        }
    
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
    
                // Update the "Check All" checkbox if it exists
                const checkAllCheckbox = document.getElementById(`${uniqueId}-check-all`);
                if (checkAllCheckbox) {
                    checkAllCheckbox.checked = values.length === attrs.options.length;
                }
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
    
    static hideWidget(node, widget, suffix = "") {
        const CONVERTED_TYPE = "converted-widget";
        if (widget.type?.startsWith(CONVERTED_TYPE)) return;
        widget.origType = widget.type;
        widget.origComputeSize = widget.computeSize;
        widget.origSerializeValue = widget.serializeValue;
        widget.computeSize = () => [0, -4]; // -4 is due to the gap litegraph adds between widgets automatically
        widget.type = CONVERTED_TYPE + suffix;
        widget.serializeValue = () => {
            // Prevent serializing the widget if we have no input linked
            if (!node.inputs) {
                return undefined;
            }
            let node_input = node.inputs.find((i) => i.widget?.name === widget.name);
    
            if (!node_input || !node_input.link) {
                return undefined;
            }
            return widget.origSerializeValue ? widget.origSerializeValue() : widget.value;
        };
    
        // Hide any linked widgets, e.g. seed+seedControl
        if (widget.linkedWidgets) {
            for (const w of widget.linkedWidgets) {
                hideWidget(node, w, ":" + widget.name);
            }
        }
    }
    
    static showWidget(widget) {
        widget.type = widget.origType;
        widget.computeSize = widget.origComputeSize;
        widget.serializeValue = widget.origSerializeValue;
    
        delete widget.origType;
        delete widget.origComputeSize;
        delete widget.origSerializeValue;
    
        // Hide any linked widgets, e.g. seed+seedControl
        if (widget.linkedWidgets) {
            for (const w of widget.linkedWidgets) {
                showWidget(w);
            }
        }
    }

    static drawSigmas(sigmas) {
        // Define the size of the canvas
        const width = 800;
        const height = 400;
    
        // Create a canvas element
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
    
        // Background
        ctx.fillStyle = '#333';  // Dark background
        ctx.fillRect(0, 0, width, height);
    
        // Normalize sigma values to fit within the canvas height
        const maxSigma = Math.max(...sigmas.map(s => s[0]));
        const minSigma = Math.min(...sigmas.map(s => s[0]));
        const range = maxSigma - minSigma;
    
        // Function to scale a sigma value to the canvas coordinates
        const scaleY = sigma => (height - 20) - (((sigma - minSigma) / range) * (height - 40));
        const scaleX = index => (index / (sigmas.length - 1)) * width;
    
        // Draw horizontal grid lines and labels
        const gridColor = '#555';
        const textColor = '#ccc';
        const numGridLines = 10;
        const gridSpacing = (height - 40) / numGridLines;
        ctx.strokeStyle = gridColor;
        ctx.lineWidth = 1;
        ctx.font = '10px Arial';
        ctx.fillStyle = textColor;
    
        for (let i = 0; i <= numGridLines; i++) {
            let y = 20 + i * gridSpacing;
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
    
            // Add text labels for grid lines
            let gridValue = maxSigma - ((i / numGridLines) * range);
            ctx.fillText(gridValue.toFixed(2), 5, y - 2);
        }
    
        // Draw the graph line
        ctx.strokeStyle = 'white'; // Line color
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(scaleX(0), scaleY(sigmas[0][0]));
    
        sigmas.forEach((sigma, index) => {
            ctx.lineTo(scaleX(index), scaleY(sigma[0]));
        });
    
        ctx.stroke();
    
        // Draw a dot at each sigma point
        ctx.fillStyle = 'red'; // Dot color
        const dotRadius = 4;
        sigmas.forEach((sigma, index) => {
            ctx.beginPath();
            ctx.arc(scaleX(index), scaleY(sigma[0]), dotRadius, 0, 2 * Math.PI);
            ctx.fill();
        });
    
        // Return the canvas content as a Base64 encoded image
        return canvas.toDataURL('image/png');
    }      
}
