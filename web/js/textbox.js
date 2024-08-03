import { SettingUtils } from './sn0w.js';
import { app } from '../../../scripts/app.js';
import { api } from '../../../scripts/api.js';

app.registerExtension({
    name: 'sn0w.Textbox',
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === 'Copy/Paste Textbox') {
            // Get textbox text
            nodeType.prototype.getTextboxText = function () {
                const textbox = this.inputEl ? this.inputEl.value : '';
                return textbox;
            };

            nodeType.prototype.updateHighlightType = function () {
                const inputEl = this.inputEl.inputEl;
                const overlayEl = this.overlayEl;
                setTextColors(inputEl, overlayEl);
                setTimeout(() => syncText(this.inputEl.inputEl, this.overlayEl), 50);
            }

            nodeType.prototype.populate = function () {
                this.inputEl = this.widgets[0];

                // prettier-ignore
                this.addWidget("button", "Copy", "Copy", () => {
                    navigator.clipboard.writeText(this.getTextboxText());
                }, { serialize: false });

                // prettier-ignore
                this.addWidget("button", "Paste", "Paste", () => {
                    navigator.clipboard.readText().then(text => {
                        this.inputEl.value = text;
                        syncText(this.inputEl.inputEl, this.overlayEl);
                    }).catch(error => {
                        console.error('Failed to read clipboard contents:', error);
                    });
                }, { serialize: false });

                // Ensure the input element's parent exists
                if (this.inputEl && this.inputEl.inputEl && this.inputEl.inputEl.parentNode) {
                    // Create overlay div for highlighting
                    this.overlayEl = document.createElement('div');
                    this.overlayEl.className = 'input-overlay';
                    this.inputEl.inputEl.parentNode.insertBefore(
                        this.overlayEl,
                        this.inputEl.inputEl
                    );

                    this.inputEl.inputEl.style.background = 'transparent';

                    addEventListeners(this);
                    addObversers(this);

                    setOverlayPosition(this.inputEl, this.overlayEl);
                    setOverlayStyle(this.inputEl, this.overlayEl);
                } else {
                    console.error('Parent node of input element is not available.');
                }
            };

            function addEventListeners(node) {
                node.inputEl.inputEl.addEventListener('input', () => {
                    syncText(node.inputEl.inputEl, node.overlayEl);
                    setOverlayStyle(node.inputEl, node.overlayEl);
                });

                node.inputEl.inputEl.addEventListener('keydown', (event) => {
                    if (
                        event.ctrlKey &&
                        (event.key === 'ArrowUp' || event.key === 'ArrowDown')
                    ) {
                        setTimeout(() => {
                            syncText(node.inputEl.inputEl, node.overlayEl);
                        }, 10);
                    }
                });
            }

            function addObversers(node) {
                const observer = new MutationObserver(() => {
                    setOverlayPosition(node.inputEl, node.overlayEl);
                });

                observer.observe(node.inputEl.inputEl, {
                    attributes: true,
                    attributeFilter: ['style'],
                    childList: true,
                    subtree: true,
                    characterData: true,
                });

                const parentObserver = new MutationObserver(() => {
                    if (!document.contains(node.inputEl.inputEl)) {
                        node.overlayEl.remove();
                    }
                });

                parentObserver.observe(node.inputEl.inputEl.parentNode, {
                    childList: true,
                });
            }

            async function setTextHighlightType(inputEl) {
                const highlightGradient = await SettingUtils.getSetting('sn0w.TextboxGradientColors');
                if (highlightGradient === null) {
                    inputEl.highlightGradient = false;
                    return;
                }

                inputEl.highlightGradient = highlightGradient;
            }

            async function setTextColors(inputEl, overlayEl) {
                const customTextboxColors = await SettingUtils.getSetting('sn0w.TextboxColors');
                setTextHighlightType(inputEl);

                const defaultColors = [
                    '#559c22',
                    '#229c57',
                    '#229c8b',
                    '#226f9c',
                    '#22479c',
                ];

                const colors = (!customTextboxColors || customTextboxColors.trim() === '')
                    ? defaultColors
                    : customTextboxColors.split('\n');

                inputEl.colors = colors.map(color =>
                    color.charAt(0) === '#' ? SettingUtils.hexToRgb(color) : color
                );
                inputEl.errorColor = 'var(--error-text)';

                syncText(inputEl, overlayEl);
                return colors;
            }

            function escapeHtml(char) {
                switch (char) {
                    case '<':
                        return '&lt;';
                    case '>':
                        return '&gt;';
                    default:
                        return char;
                }
            }

            function interpolateColor(color1, color2, factor) {
                const rgb1 = color1.match(/\d+/g).map(Number);
                const rgb2 = color2.match(/\d+/g).map(Number);

                const r = Math.round(rgb1[0] + factor * (rgb2[0] - rgb1[0]));
                const g = Math.round(rgb1[1] + factor * (rgb2[1] - rgb1[1]));
                const b = Math.round(rgb1[2] + factor * (rgb2[2] - rgb1[2]));

                return `rgb(${r}, ${g}, ${b})`;
            }

            function easeInOutCubic(t) {
                return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
            }

            function charToType(char) {
                switch(char) {
                    case '<':
                        return '-lora';
                    case 'e':
                        return '-embedding';
                    default:
                        return '';
                }
            }

            function extractLoraName(text, currentIndex) {
                const loraPrefix = "lora:";
                const startIndex = text.lastIndexOf(loraPrefix, currentIndex) + loraPrefix.length;

                // Find the end of the LoRA name (next space, comma, or ".safetensors")
                let endIndex = text.indexOf(' ', startIndex);
                const commaIndex = text.indexOf(',', startIndex);
                const safetensorsIndex = text.indexOf('.safetensors', startIndex);

                if (endIndex === -1 || (commaIndex !== -1 && commaIndex < endIndex)) {
                    endIndex = commaIndex;
                }
                if (endIndex === -1 || (safetensorsIndex !== -1 && safetensorsIndex < endIndex)) {
                    endIndex = safetensorsIndex;
                }

                // If there's no space, comma, or ".safetensors" after the LoRA name, consider the end of the text
                const loraName = endIndex === -1 ? text.slice(startIndex) : text.slice(startIndex, endIndex);
                return loraName;
            }

            function validateName(validFiles, name) {
                if (!validFiles) {
                    console.error('Valid names not defined or not an array.');
                    return false;
                }

                if (validFiles.includes(name)) {
                    return true;
                } else {
                    return false;
                }
            }

            function processTags(tags) {
                let returnArray = [];
                tags.forEach(tag => {
                    returnArray.push(processTag(tag));
                })
                return returnArray;
            }

            function processTag(tag) {
                let trimmedTag = tag.trim();

                // Remove HTML tags
                trimmedTag = trimmedTag.replace(/<[^>]*>/g, '');

                // Remove the first character if it is a parenthesis
                if (trimmedTag.startsWith('(')) {
                    trimmedTag = trimmedTag.substring(1).trim();
                }

                // Remove everything after a colon
                const colonIndex = trimmedTag.indexOf(':');
                if (colonIndex !== -1) {
                    trimmedTag = trimmedTag.substring(0, colonIndex).trim();
                }

                return trimmedTag;
            }

            const charPairs = {
                '(': ')',
                '<': '>',
            };

            async function syncText(inputEl, overlayEl, tries = 1) {
                const text = inputEl.value;
                overlayEl.textContent = text;

                const colors = inputEl.colors;
                const errorColor = inputEl.errorColor;
                const shouldHighlightGradient = inputEl.highlightGradient;
                const loraColor = colors ? colors[0] : undefined;

                if (!colors || !errorColor || !loraColor || shouldHighlightGradient == undefined) {
                    if (tries < 5) {
                        setTimeout(() => syncText(inputEl, overlayEl, tries++), tries * 5);
                    }
                    return;
                }

                let uniqueIdCounter = 0;
                const generateUniqueId = (type = "") => `span-${uniqueIdCounter++}${type}`;

                let nestingLevel = 0;
                let highlightedText = '';
                let lastIndex = 0;
                let spanStack = [];
                const uniqueIdMap = new Map();

                const extractTags = (text) => {
                    let tags = text.split(',').map(tag => tag.trim());
                    tags = processTags(tags);
                    const tagCounts = new Map();

                    tags.forEach(tag => {
                        tagCounts.set(tag, (tagCounts.get(tag) || 0) + 1);
                    });

                    return { tags, tagCounts };
                };

                const { tags, tagCounts } = extractTags(text);

                /*
                 * This loop iterates over each character in the `text` string to apply syntax highlighting and handle special cases.
                 * - lastIndex: index of the last processed character, used to slice text segments.
                 * - spanStack: stack to manage opened spans, storing their ids, start positions, original colors, and characters.
                */
                for (let i = 0; i < text.length; i++) {
                    const char = text[i].toLowerCase();

                    // Handle escape characters
                    if (char === '\\' && i + 1 < text.length && (text[i + 1] === '(' || text[i + 1] === ')')) {
                        i++;
                        continue;
                    }

                    // Handle wrong escape characters
                    if (char === '/' && i + 1 < text.length && (text[i + 1] === '(' || text[i + 1] === ')')) {
                        highlightedText += text.slice(lastIndex, i) + `<span style="background-color: ${errorColor};">/</span>`;
                        console.error(`Replace "${char}" at char ${i} with "\\"`);
                        lastIndex = i + 1;
                        continue;
                    }

                    let color = colors[nestingLevel % colors.length];
                    let uniqueId = generateUniqueId(charToType(char));
                    if (inputEl.highlightGradient === true) {
                        color = `id-${uniqueId}`;
                    }
                    switch(char) {
                        case '(':
                        case '<':
                            highlightedText += text.slice(lastIndex, i) + `<span id="${uniqueId}" style="background-color: ${color};">${escapeHtml(char)}`;
                            spanStack.push({ id: uniqueId, start: highlightedText.length, originalSpan: `<span id="${uniqueId}" style="background-color: ${color};">`, nestingLevel, originalColor: color, originalChar: char });
                            nestingLevel++;
                            lastIndex = i + 1;
                            break;
                        case 'e':
                            let embeddingColor = colors[0];
                            const embeddingPrefix = "embedding:";

                            // Check if the text starts with "embedding:" at position i
                            if (text.toLowerCase().startsWith(embeddingPrefix, i)) {
                                // Find the end of the embedding (next space or comma)
                                let endIndex = i + embeddingPrefix.length;
                                while (endIndex < text.length && text[endIndex] !== ' ' && text[endIndex] !== ',') {
                                    endIndex++;
                                }

                                // Get the full embedding text
                                const embeddingText = text.slice(i, endIndex);
                                if (validateName(inputEl.validEmbeddings, embeddingText.split(":")[1]) === false) {
                                    embeddingColor = errorColor;
                                }
                                const wrappedEmbedding = `<span id="${uniqueId}" style="background-color: ${embeddingColor};">${escapeHtml(embeddingText)}</span>`;
                                highlightedText += text.slice(lastIndex, i) + wrappedEmbedding;
                                lastIndex = i + embeddingText.length;
                            }
                            break;
                        case ')':
                        case '>':
                            if (nestingLevel > 0) {
                                const { id, originalColor, originalChar } = spanStack[spanStack.length - 1];
                                if (charPairs[originalChar] === char) {
                                    spanStack.pop();
                                    highlightedText += text.slice(lastIndex, i) + `${escapeHtml(char)}</span>`;
                                    nestingLevel--;

                                    // Extract and validate the LoRA name
                                    if (id.endsWith('lora')) {
                                        const loraName = extractLoraName(text, i);
                                        if (validateName(inputEl.validLoras, loraName) === false) {
                                            uniqueIdMap.set(id, [errorColor, originalColor]);
                                            lastIndex = i + 1;
                                            continue;
                                        }
                                    }

                                    if (inputEl.highlightGradient === true || id.endsWith('lora')) {
                                        // Check for the strength
                                        const strengthText = text.slice(Math.max(0, i - 10), i);
                                        const match = strengthText.match(/(\d+(\.\d+)?)\s*$/);
                                        if (match) {
                                            const strength = parseFloat(match[1]);
                                            const clampedStrength = Math.max(0, Math.min(2, strength));
                                            const normalizedStrength = clampedStrength / 2;
                                            const newColor = interpolateColor(colors[0], colors[colors.length - 1], easeInOutCubic(normalizedStrength));
                                            uniqueIdMap.set(id, [newColor, originalColor]);
                                        } else {
                                            uniqueIdMap.set(id, [interpolateColor(colors[0], colors[colors.length - 1], 0.5), originalColor]);
                                        }
                                    }
                                    lastIndex = i + 1;
                                }
                            }
                            break;
                    }
                }

                highlightedText += text.slice(lastIndex);

                if (nestingLevel > 0) {
                    // Apply red highlight to the unclosed spans
                    while (spanStack.length > 0) {
                        const spanData = spanStack.pop();
                        if (spanData) {
                            const { id, start, originalSpan } = spanData;
                            const errorSpanTag = `<span id="${id}" style="background-color: ${errorColor};">`;

                            if (originalSpan) {
                                highlightedText = highlightedText.replace(originalSpan, errorSpanTag);
                                highlightedText += `</span>`;
                            }
                        }
                    }
                }

                // Apply the updated colors to the highlighted text
                uniqueIdMap.forEach((colors, id) => {
                    const [newColor, originalColor] = [colors[0], colors[1]];
                    highlightedText = highlightedText.replace(`id="${id}" style="background-color: ${originalColor};"`, `id="${id}" style="background-color: ${newColor};"`);
                });

                // Highlight duplicate tags
                highlightedText.split(/(,)/).map(segment => {
                    if (segment === ',') {
                        return segment;
                    }

                    const trimmedSegment = processTag(segment);

                    // Check for duplicates
                    if (tagCounts.get(trimmedSegment) > 1) {
                        highlightedText = highlightedText.replaceAll(trimmedSegment, `<span style="background-color: ${errorColor};">${trimmedSegment}</span>`)
                    }
                }).join('');

                overlayEl.innerHTML = highlightedText;
            }

            function setOverlayPosition(inputEl, overlayEl) {
                const textareaStyle = window.getComputedStyle(inputEl.inputEl);
                overlayEl.style.left = textareaStyle.left;
                overlayEl.style.top = textareaStyle.top;
                overlayEl.style.width = textareaStyle.width;
                overlayEl.style.height = textareaStyle.height;
                overlayEl.style.display = textareaStyle.display;
                overlayEl.style.transform = textareaStyle.transform;
                overlayEl.style.transformOrigin = textareaStyle.transformOrigin;
            }

            function setOverlayStyle(inputEl, overlayEl) {
                const textareaStyle = window.getComputedStyle(inputEl.inputEl);
                overlayEl.style.backgroundColor = 'var(--comfy-input-bg)';
                overlayEl.style.position = 'absolute';
                overlayEl.style.fontFamily = textareaStyle.fontFamily;
                overlayEl.style.fontSize = textareaStyle.fontSize;
                overlayEl.style.fontWeight = textareaStyle.fontWeight;
                overlayEl.style.lineHeight = textareaStyle.lineHeight;
                overlayEl.style.letterSpacing = textareaStyle.letterSpacing;
                overlayEl.style.whiteSpace = textareaStyle.whiteSpace;
                overlayEl.style.color = 'rgba(0,0,0,0)';
                overlayEl.style.padding = textareaStyle.padding;
                overlayEl.style.boxSizing = textareaStyle.boxSizing;
                overlayEl.style.zIndex = '1';
                overlayEl.style.pointerEvents = 'none';
                overlayEl.style.color = 'transparent';
                overlayEl.style.overflow = 'hidden';
                overlayEl.style.whiteSpace = 'pre-wrap';
                overlayEl.style.wordWrap = 'break-word';
            }

            async function setValidFiles(inputEl) {
                inputEl.validLoras = await getValidFiles("loras");
                inputEl.validEmbeddings = await getValidFiles("embeddings");
            }

            async function getValidFiles(type) {
                const apiRequest = await api.fetchApi(`${SettingUtils.API_PREFIX}/${type}`, {
                    method: "GET",
                })
                if (!apiRequest.ok) {
                    console.error('API request failed:', apiRequest.statusText);
                } else {
                    const responseBody = await apiRequest.json();
                    return responseBody;
                }
            }

            nodeType.prototype.onNodeCreated = function () {
                this.populate();
                setTextColors(this.inputEl.inputEl, this.overlayEl);
                setValidFiles(this.inputEl.inputEl);
                this.getTextboxText = this.getTextboxText.bind(this);
            };
        }
    },
});

const settingsDefinitions = [
    {
        id: 'sn0w.TextboxColors',
        name: '[Sn0w] Custom Textbox Colors',
        type: SettingUtils.createMultilineSetting,
        defaultValue: '#559c22\n#229c57\n#229c8b\n#226f9c\n#22479c',
        attrs: { tooltip: 'A list of either rgb or hex colors, one color per line.' },
        onChange: () => {
            const nodes = app.graph._nodes.filter(node => node.type === 'Copy/Paste Textbox');
            nodes.forEach(node => {
                node.updateHighlightType();
            });
        },
    },
    {
        id: 'sn0w.TextboxGradientColors',
        name: '[Sn0w] Custom Textbox Gradient Highlight',
        type: 'boolean',
        defaultValue: false,
        tooltip: 'Makes the textbox highlighting be a gradient between the first and last color based on the strength of the selection.',
        onChange: () => {
            const nodes = app.graph._nodes.filter(node => node.type === 'Copy/Paste Textbox');
            nodes.forEach(node => {
                node.updateHighlightType();
            });
        },
    }
];

const registerSetting = (settingDefinition) => {
    const extension = {
        name: settingDefinition.id,
        init() {
            const setting = app.ui.settings.addSetting({
                id: settingDefinition.id,
                name: settingDefinition.name,
                type: settingDefinition.type,
                defaultValue: settingDefinition.defaultValue,
                tooltip: settingDefinition.tooltip,
                attrs: settingDefinition.attrs,
                onChange: settingDefinition.onChange,
            });
        },
    };
    app.registerExtension(extension);
};

// Register settings
settingsDefinitions.forEach((setting) => {
    registerSetting(setting);
});
