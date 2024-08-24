import { app } from '../../../scripts/app.js';
import { api } from '../../../scripts/api.js';
import { $el } from '../../../scripts/ui.js'

export class SettingUtils {
    static API_PREFIX = '/sn0w';
    static settingsCache = {};

    static async getSetting(url, defaultValue = null) {
        const currentTime = Date.now();
        const cacheEntry = this.settingsCache[url];

        // Check if the cache entry exists and is still valid (not older than 1 seconds)
        if (cacheEntry && currentTime - cacheEntry.timestamp < 1000) {
            return cacheEntry.data;
        }

        try {
            const settingUrl = `/settings/${url}`;
            const response = await fetch(settingUrl);
            if (!response.ok) {
                return defaultValue;
            }
            const data = await response.json();
            if (data == null) {
                return defaultValue;
            }

            // Store the fetched setting in the cache with the current timestamp
            this.settingsCache[url] = {
                data: data,
                timestamp: currentTime
            };

            SettingUtils.logSn0w(`Got setting: ${url}`, "debug", "setting", data);
            return data;
        } catch (error) {
            console.error('There was a problem with the fetch operation:', error);
            return defaultValue;
        }
    }

    static async getMultipleSettings(settingsArray) {
        // Create an array of promises using getSetting with the corresponding default values
        const promises = settingsArray.map(({ url, defaultValue }) =>
            this.getSetting(url, defaultValue)
        );

        try {
            const results = await Promise.all(promises);

            // Convert the results to a Map or a plain object where each URL is the key
            const settingsMap = {};
            settingsArray.forEach(({ url }, index) => {
                settingsMap[url] = results[index];
            });

            return settingsMap;
        } catch (error) {
            console.error('There was a problem with one of the fetch operations:', error);
            return null;
        }
    }

    static async fetchApi(route, options) {
        if (!options) {
			options = {};
		}
		if (!options.headers) {
			options.headers = {};
		}

        options.cache = 'no-store';

        try {
            const response = await fetch(route, options);
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
            await api.storeSetting(setting, existingList);
        } catch (error) {
            console.error('Error updating settings:', error);
        }
    }

    static registerSetting = (settingDefinition) => {
        const extension = {
            name: settingDefinition.id,
            init() {
                const setting = app.ui.settings.addSetting({
                    ...settingDefinition, // Spread all properties from settingDefinition
                });
            },
        };
        app.registerExtension(extension);
    };

    static createMultilineSetting(name, setter, value, attrs) {
        // Ensure that tooltip has a default value if not provided
        const htmlID = `${name.replaceAll(' ', '').replaceAll('[', '').replaceAll(']', '-')}`;

        // Create the textarea element
        const textarea = $el('textarea', {
            value,
            id: htmlID,
            oninput: (e) => {
                adjustHeight();
            },
            className: "p-inputtext",
            style: {
                width: "100%",
                resize: "none",
            },
            ...attrs
        });

        const maxLines = 10;

        const adjustHeight = () => {
            requestAnimationFrame(() => {
                const parentDiv = textarea.parentElement;
                if (parentDiv != null) {
                    parentDiv.style.width = "100%";

                    const id = parentDiv.id;
                    if (id != null) {
                        api.storeSetting(id, textarea.value);
                    }
                }

                textarea.style.height = ''; // Allow to shrink
                const lines = textarea.value.split('\n').length;
                const scrollHeight = textarea.scrollHeight + 3;
                if (lines > maxLines) {
                    const height = (scrollHeight / lines) * maxLines
                    textarea.setAttribute(
                        'style',
                        `width: 100%; height: ${height}px; resize: none;`
                    );
                    return;
                }
                textarea.setAttribute('style', `width: 100%; height: ${scrollHeight}px; resize: none;`);
            });
        };

        adjustHeight();

        return textarea;
    }

    static createCheckboxSetting(name, setter, value, attrs) {
        // Define the threshold for showing the "Check All" checkbox
        const threshold = 10;
        const hideThreshold = 5;

        const tr = document.createElement('tr');
        const tdInput = document.createElement('td');

        // Generate a unique ID for the setting container
        const uniqueId = `${name.replaceAll(' ', '').replaceAll('[', '').replaceAll(']', '-')}`;

        // Checkbox container
        const checkboxContainer = document.createElement('div');
        checkboxContainer.id = uniqueId;
        //checkboxContainer.style.padding = "5px";
        checkboxContainer.style.display = 'block'; // Ensure it is initially visible

        // Hide button
        if (attrs.options.length > hideThreshold) {
            const hideButton = document.createElement('button');
            hideButton.textContent = 'Show';
            checkboxContainer.style.display = 'none';
            hideButton.onclick = () => {
                checkboxContainer.style.display =
                    checkboxContainer.style.display === 'none' ? 'block' : 'none';
                hideButton.textContent =
                    checkboxContainer.style.display === 'none' ? 'Show' : 'Hide';
                hideButton.style.marginBottom =
                    checkboxContainer.style.display === 'none' ? '0px' : '5px';
            };
            hideButton.style.width = '100%';

            // Append the hide button before the checkboxes
            tdInput.appendChild(hideButton);
        }

        // Initialize values array based on the default value
        let values = Array.isArray(value) ? value : [value];

        // Check if the number of options exceeds the threshold
        if (attrs.options.length > threshold) {
            // Create search textbox
            const searchContainer = document.createElement('div');
            const searchInput = document.createElement('input');
            searchInput.type = 'text';
            searchInput.placeholder = 'Search...';
            searchInput.style.width = '100%';

            searchContainer.appendChild(searchInput);
            checkboxContainer.appendChild(searchContainer);

            // Create "Check All" checkbox
            const checkAllContainer = document.createElement('div');
            const checkAllCheckbox = document.createElement('input');
            const checkAllLabel = document.createElement('label');
            const checkAllId = `${uniqueId}-check-all`;

            checkAllCheckbox.type = 'checkbox';
            checkAllCheckbox.id = checkAllId;
            checkAllCheckbox.onchange = () => {
                const allCheckboxes = checkboxContainer.querySelectorAll('input[type="checkbox"]');
                allCheckboxes.forEach((checkbox) => {
                    if (checkbox !== checkAllCheckbox) {
                        checkbox.checked = checkAllCheckbox.checked;
                        const optionValue = checkbox.id.split('-').pop();
                        if (checkAllCheckbox.checked && !values.includes(optionValue)) {
                            values.push(optionValue);
                        } else if (!checkAllCheckbox.checked && values.includes(optionValue)) {
                            values = values.filter((v) => v !== optionValue);
                        }
                    }
                });
                setter(values); // Update the setting with the current array of selected values
            };

            checkAllLabel.setAttribute('for', checkAllId);
            checkAllLabel.textContent = 'Check All';
            checkAllLabel.style.marginRight = '10px';

            checkAllContainer.style.borderBottom = '1px solid var(--border-color)';
            checkAllContainer.style.paddingBottom = '4px';
            checkAllContainer.style.marginBottom = '5px';

            checkAllContainer.appendChild(checkAllCheckbox);
            checkAllContainer.appendChild(checkAllLabel);
            checkboxContainer.appendChild(checkAllContainer);

            // Filter checkboxes based on search input
            searchInput.addEventListener('input', () => {
                const searchText = searchInput.value.toLowerCase();
                attrs.options.forEach((option) => {
                    const checkbox = document.getElementById(`${uniqueId}-${option.value}`);
                    const label = checkbox.nextSibling;
                    if (option.label.toLowerCase().includes(searchText)) {
                        checkbox.parentElement.style.display = '';
                    } else {
                        checkbox.parentElement.style.display = 'none';
                    }
                });
            });
        }

        // Create checkboxes based on the options provided in attrs
        attrs.options.forEach((option) => {
            const checkbox = document.createElement('input');
            const checkboxLabel = document.createElement('label');
            const checkboxId = `${uniqueId}-${option.value}`;

            checkbox.type = 'checkbox';
            checkbox.id = checkboxId;
            checkbox.checked = values.includes(option.value);
            checkbox.onchange = () => {
                if (checkbox.checked && !values.includes(option.value)) {
                    values.push(option.value);
                } else if (!checkbox.checked && values.includes(option.value)) {
                    values = values.filter((v) => v !== option.value);
                }
                setter(values); // Update the setting with the current array of selected values

                // Update the "Check All" checkbox if it exists
                const checkAllCheckbox = document.getElementById(`${uniqueId}-check-all`);
                if (checkAllCheckbox) {
                    checkAllCheckbox.checked = values.length === attrs.options.length;
                }
            };

            checkboxLabel.setAttribute('for', checkboxId);
            checkboxLabel.textContent = option.label;
            checkboxLabel.style.marginRight = '10px';

            const wrapper = document.createElement('div');
            wrapper.appendChild(checkbox);
            wrapper.appendChild(checkboxLabel);
            checkboxContainer.appendChild(wrapper);
        });

        tdInput.appendChild(checkboxContainer);

        tr.appendChild(tdInput);

        const tooltip = attrs.tooltip;

        // Set tooltip if provided
        if (tooltip) {
            tr.title = tooltip;
            label.className = 'comfy-tooltip-indicator';
        }

        return tr;
    }

    // WIDGETS
    static hideWidget(node, widget, suffix = '') {
        const CONVERTED_TYPE = 'converted-widget';
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
                hideWidget(node, w, ':' + widget.name);
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

    async #invokeExtensionsAsync(method, graphCanvas, ...args) {
        return await Promise.all(
            graphCanvas.extensions.map(async (ext) => {
                if (method in ext) {
                    try {
                        return await ext[method](...args, graphCanvas);
                    } catch (error) {
                        console.error(
                            `Error calling extension '${ext.name}' method '${method}'`,
                            { error },
                            { extension: ext },
                            { args }
                        );
                    }
                }
            })
        );
    }

    async refreshComboInSingleNode(graphCanvas, nodeName) {
        const defs = await api.getNodeDefs();

        // Find the node definition by name
        let nodeDef = null;
        for (const def of Object.values(defs)) {
            if (def.name === nodeName) {
                nodeDef = def;
                break;
            }
        }

        if (!nodeDef) {
            console.error(`Node definition with name ${nodeName} not found`);
            return;
        }

        // Find the specific node in the graph by name
        let node = null;
        for (const graphNode of Object.values(graphCanvas.graph._nodes)) {
            if (graphNode.type === nodeDef.name) {
                node = graphNode;
                break;
            }
        }

        if (!node) {
            console.warn(`Node with name ${nodeName} not found in the graph`);
            return;
        }

        for (let nodeNum in graphCanvas.graph._nodes) {
            const node = graphCanvas.graph._nodes[nodeNum];
            if (node.title == nodeName) {
                const def = defs[node.type];

                // Allow primitive nodes to handle refresh
                node.refreshComboInNode?.(defs);

                if (!def) continue;

                for (const widgetNum in node.widgets) {
                    const widget = node.widgets[widgetNum];
                    if (
                        widget.type == 'combo' &&
                        def['input']['required'][widget.name] !== undefined
                    ) {
                        widget.options.values = def['input']['required'][widget.name][0];

                        if (
                            widget.name != 'image' &&
                            !widget.options.values.includes(widget.value)
                        ) {
                            widget.value = widget.options.values[0];
                            widget.callback(widget.value);
                        }
                    }
                }
            }
        }

        await this.#invokeExtensionsAsync('refreshComboInSingleNodeByName', graphCanvas, defs);
    }

    static async addStarsToFavourited(menuEntries, existingList) {
        const highlightLora = await SettingUtils.getSetting('sn0w.HighlightFavourite');

        const root = document.documentElement;
        const comfyMenuBgColor = SettingUtils.hexToRgb(
            getComputedStyle(root).getPropertyValue('--comfy-menu-bg').trim()
        );

        // Function to check and update the background color
        const checkAndUpdateBackgroundColor = (entry, currentBgColor) => {
            if (highlightLora && currentBgColor == comfyMenuBgColor) {
                entry.setAttribute('style', 'background-color: green !important');
                // Ensure the entry uses flexbox for alignment
                entry.style.display = 'flex';
                entry.style.alignItems = 'center';
            }
        };
        let arr = []
        let starred = [0, []];
        menuEntries.forEach((entry) => {
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
                    starred[0]++;
                    starred[1].push(filename);
                }

                // Initial background color check
                const currentBgColor = window.getComputedStyle(entry).backgroundColor;
                checkAndUpdateBackgroundColor(entry, currentBgColor);
            }
            SettingUtils.logSn0w(`Total Favourited Items: ${starred[0]}`, "debug", "node", starred[1])
        });
    }

    static observeContextMenu(existingList) {
        const handleMutations = SettingUtils.leadingEdgeDebounce(function(mutations) {
            const litecontextmenu = document.getElementsByClassName('litecontextmenu')[0];
            if (litecontextmenu) {
                const menuEntries = litecontextmenu.querySelectorAll('.litemenu-entry');
                const menuEntriesArray = Array.from(menuEntries);
                const containsItemFromList = menuEntriesArray.some(entry => {
                    const value = entry.value;
                    return existingList.includes(value);
                });
                if (containsItemFromList) {
                    SettingUtils.addStarsToFavourited(menuEntries, existingList);
                }
            }
        }, 100);

        const observer = new MutationObserver(handleMutations);

        observer.observe(document, {
            attributes: false,
            childList: true,
            characterData: false,
            subtree: true,
        });
    }

    // MISC
    static debounce(func, delay) {
        let debounceTimer;
        return function () {
            const context = this;
            const args = arguments;
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => func.apply(context, args), delay);
        };
    }

    static leadingEdgeDebounce(func, wait) {
        let timeout;
        let lastCallTime = 0;

        return function(...args) {
            const now = Date.now();

            // If the last call was longer ago than the wait period, reset the timeout
            if (now - lastCallTime > wait) {
                lastCallTime = now;
                func.apply(this, args);  // Call the function immediately
            }

            clearTimeout(timeout);  // Clear any previous timeout

            // Set a new timeout that will reset `lastCallTime` after the wait period
            timeout = setTimeout(() => {
                lastCallTime = 0;
            }, wait);
        };
    }

    static async logSn0w(message, type, category = "", detailMessage = "") {
        const loggingLevels = await SettingUtils.getSetting("sn0w.LoggingLevel");
        const alwaysLog = ["emergency", "alert", "critical", "error"]
        const logLevel = type.toLowerCase();

        if (!alwaysLog.includes(logLevel) && !loggingLevels.includes(type.toUpperCase())) {
            console.log("dont log")
            return;
        }

        const prefix = "sn0w";
        const generalCss = 'color: white; padding: 2px 6px 2px 4px; font-weight: lighter;'
        let customCSS = generalCss + ' border-radius: 3px;';

        const logColors = {
            "error": "#c50f1f",
            "warning": "#c19c00",
        };

        const categoryColors = {
            "api": "#c19c00",
            "lora": "#3a96dd",
        }

        const color = logColors[logLevel] || "#881798";
        const categoryCSS = category ? `background-color: ${categoryColors[category.toLowerCase()] || "#13a10e"}; border-radius: 0 3px 3px 0; margin-left: -5px;` : '';
        const logMessage = category
            ? [`%c${prefix}%c${category}`, `${customCSS.replace("6px", "10px")} background-color: ${color};`, `${generalCss} ${categoryCSS}`, message] // Category
            : [`%c${prefix}`, `${customCSS} background-color: ${color};`, message]; // No Category

        console.groupCollapsed(...logMessage);
        if (detailMessage != "") {
            console.log(detailMessage);
        }
        console.trace();
        console.groupEnd();
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
        ctx.fillStyle = '#333'; // Dark background
        ctx.fillRect(0, 0, width, height);

        // Normalize sigma values to fit within the canvas height
        const maxSigma = Math.max(...sigmas.map((s) => s[0]));
        const minSigma = Math.min(...sigmas.map((s) => s[0]));
        const range = maxSigma - minSigma;

        // Function to scale a sigma value to the canvas coordinates
        const scaleY = (sigma) => height - 20 - ((sigma - minSigma) / range) * (height - 40);
        const scaleX = (index) => (index / (sigmas.length - 1)) * width;

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
            let gridValue = maxSigma - (i / numGridLines) * range;
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
