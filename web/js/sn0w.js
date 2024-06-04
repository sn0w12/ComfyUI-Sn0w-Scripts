import { api } from '../../../scripts/api.js';

export class SettingUtils {
    static API_PREFIX = '/sn0w';
    
    // SETTINGS
    static async getSetting(url) {
        try {
            const settingUrl = `/settings/${url}`
            const response = await fetch(settingUrl);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('There was a problem with the fetch operation:', error);
        }
    }

    // Callback function to add or remove the filename from the settings list
    static async toggleFavourite(existingList, filename, setting) {
        try {
            // Check if the filename is already in the list
            const index = existingList.indexOf(filename);
            if (index === -1) {
                // Add the new filename to the list
                existingList.push(filename);
            } else {
                // Remove the filename from the list
                existingList.splice(index, 1);
            }

            // Store the updated list back in the settings
            await api.storeSetting(setting, existingList)
        } catch (error) {
            console.error('Error updating settings:', error);
        }
    }

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
        // Define the threshold for showing the "Check All" checkbox
        const threshold = 10;
        const hideThreshold = 5;

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
        //checkboxContainer.style.padding = "5px";
        checkboxContainer.style.display = "block"; // Ensure it is initially visible
    
        // Hide button
        if (attrs.options.length > hideThreshold) {
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
        }
    
    
        // Initialize values array based on the default value
        let values = Array.isArray(value) ? value : [value];
    
        // Check if the number of options exceeds the threshold
        if (attrs.options.length > threshold) {
            // Create search textbox
            const searchContainer = document.createElement("div");
            const searchInput = document.createElement("input");
            searchInput.type = "text";
            searchInput.placeholder = "Search...";
            searchInput.style.width = "100%";

            searchContainer.appendChild(searchInput);
            checkboxContainer.appendChild(searchContainer);

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
                    if (checkbox !== checkAllCheckbox) {
                        checkbox.checked = checkAllCheckbox.checked;
                        const optionValue = checkbox.id.split('-').pop();
                        if (checkAllCheckbox.checked && !values.includes(optionValue)) {
                            values.push(optionValue);
                        } else if (!checkAllCheckbox.checked && values.includes(optionValue)) {
                            values = values.filter(v => v !== optionValue);
                        }
                    }
                });
                setter(values); // Update the setting with the current array of selected values
            };

            checkAllLabel.setAttribute("for", checkAllId);
            checkAllLabel.textContent = "Check All";
            checkAllLabel.style.marginRight = "10px";

            checkAllContainer.style.borderBottom = "1px solid var(--border-color)";
            checkAllContainer.style.paddingBottom = "4px";
            checkAllContainer.style.marginBottom = "5px";

            checkAllContainer.appendChild(checkAllCheckbox);
            checkAllContainer.appendChild(checkAllLabel);
            checkboxContainer.appendChild(checkAllContainer);

            // Filter checkboxes based on search input
            searchInput.addEventListener("input", () => {
                const searchText = searchInput.value.toLowerCase();
                attrs.options.forEach(option => {
                    const checkbox = document.getElementById(`${uniqueId}-${option.value}`);
                    const label = checkbox.nextSibling;
                    if (option.label.toLowerCase().includes(searchText)) {
                        checkbox.parentElement.style.display = "";
                    } else {
                        checkbox.parentElement.style.display = "none";
                    }
                });
            });
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
    
    // WIDGETS
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

    static async addStarsToFavourited(existingList) {
        const menuEntries = document.querySelectorAll('.litemenu-entry');
        const highlightLora = await SettingUtils.getSetting("sn0w.HighlightFavourite");
    
        const root = document.documentElement;
        const comfyMenuBgColor = SettingUtils.hexToRgb(getComputedStyle(root).getPropertyValue('--comfy-menu-bg').trim());
    
        menuEntries.forEach(entry => {
            const value = entry.getAttribute('data-value');
            let filename = value;
            if (value !== null && value.includes('\\')) {
                const pathArray = value.split('\\');
                filename = pathArray[pathArray.length - 1];
            }
            
            if (existingList.includes(filename)) {
                // Create star element
                const star = document.createElement('span');
                star.innerHTML = '★';
                star.style.marginLeft = 'auto'; // Push the star to the right
                star.style.alignSelf = 'center'; // Center the star vertically
    
                // Ensure the entry uses flexbox for alignment
                entry.style.display = 'flex';
                entry.style.alignItems = 'center';
    
                // Check if star is already added to avoid duplication
                if (!entry.querySelector('span')) {
                    entry.appendChild(star);
                }
    
                // If user has selected to highlight loras and the lora doesn't already have a specified background color
                const currentBgColor = window.getComputedStyle(entry).backgroundColor;
                if (highlightLora && currentBgColor === comfyMenuBgColor) {
                    entry.setAttribute( 'style', 'background-color: green !important' );
                }
            }
        });
    }

    // MISC
    static debounce(func, delay) {
        let debounceTimer;
        return function() {
            const context = this;
            const args = arguments;
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => func.apply(context, args), delay);
        };
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
    
    static hexToRgb(hex) {
        // Remove the hash at the start if it's there
        hex = hex.replace(/^#/, '');
    
        // Parse the r, g, b values
        let bigint = parseInt(hex, 16);
        let r = (bigint >> 16) & 255;
        let g = (bigint >> 8) & 255;
        let b = bigint & 255;
    
        return `rgb(${r}, ${g}, ${b})`;
    }
}
