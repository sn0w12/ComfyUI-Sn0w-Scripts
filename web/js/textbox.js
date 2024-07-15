import { SettingUtils } from './sn0w.js';
import { app } from '../../../scripts/app.js';

app.registerExtension({
    name: 'sn0w.Textbox',
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === 'Copy/Paste Textbox') {
            // Get textbox text
            nodeType.prototype.getTextboxText = function () {
                const textbox = this.inputEl ? this.inputEl.value : '';
                return textbox;
            };

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

                    // Sync text initially and on input
                    this.inputEl.inputEl.addEventListener('input', () => {
                        syncText(this.inputEl.inputEl, this.overlayEl);
                        setOverlayStyle(this.inputEl, this.overlayEl);
                    });

                    const observer = new MutationObserver(() => {
                        setOverlayPosition(this.inputEl, this.overlayEl);
                    });

                    observer.observe(this.inputEl.inputEl, {
                        attributes: true,
                        attributeFilter: ['style'],
                        childList: true,
                        subtree: true,
                        characterData: true,
                    });

                    const parentObserver = new MutationObserver(() => {
                        if (!document.contains(this.inputEl.inputEl)) {
                            this.overlayEl.remove();
                        }
                    });

                    parentObserver.observe(this.inputEl.inputEl.parentNode, {
                        childList: true,
                    });

                    this.inputEl.inputEl.addEventListener('keydown', (event) => {
                        if (
                            event.ctrlKey &&
                            (event.key === 'ArrowUp' || event.key === 'ArrowDown')
                        ) {
                            setTimeout(() => {
                                syncText(this.inputEl.inputEl, this.overlayEl);
                            }, 10);
                        }
                    });

                    setTimeout(() => {
                        setOverlayPosition(this.inputEl, this.overlayEl);
                        setOverlayStyle(this.inputEl, this.overlayEl);
                    }, 10);
                } else {
                    console.error('Parent node of input element is not available.');
                }
            };

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
                if (
                    customTextboxColors == null ||
                    (customTextboxColors.length === 1 && customTextboxColors[0] === '') ||
                    customTextboxColors == '' || customTextboxColors.length == 0
                ) {
                    const defaultColors = [
                        'rgba(0, 255, 0, 0.5)',
                        'rgba(0, 0, 255, 0.5)',
                        'rgba(255, 0, 0, 0.5)',
                        'rgba(255, 255, 0, 0.5)',
                    ];
                    inputEl.colors = defaultColors;
                    inputEl.errorColor = 'var(--error-text)';
                    syncText(inputEl, overlayEl);
                    return defaultColors;
                }

                let colors = customTextboxColors.split('\n');
                colors = colors.map((color) => {
                    if (color.charAt(0) == '#') {
                        return SettingUtils.hexToRgb(color);
                    }
                    return color;
                });
                inputEl.colors = colors;
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

            async function syncText(inputEl, overlayEl) {
                const text = inputEl.value;
                overlayEl.textContent = text;

                const colors = inputEl.colors;
                const errorColor = inputEl.errorColor;
                const shouldHighlightGradient = inputEl.highlightGradient;
                const loraColor = colors ? colors[0] : undefined;

                if (!colors || !errorColor || !loraColor || !shouldHighlightGradient) {
                    setTimeout(() => syncText(inputEl, overlayEl), 5);
                    return;
                }

                let uniqueIdCounter = 0;
                const generateUniqueId = () => `unique-span-${uniqueIdCounter++}`;

                let nestingLevel = 0;
                let highlightedText = '';
                let lastIndex = 0;
                let spanStack = [];
                const uniqueIdMap = new Map();

                for (let i = 0; i < text.length; i++) {
                    const char = text[i];

                    // Handle escape characters
                    if (char === '\\' && i + 1 < text.length && (text[i + 1] === '(' || text[i + 1] === ')')) {
                        i++;
                        continue;
                    }

                    // Handle wrong escape characters
                    if (char === '/' && i + 1 < text.length && (text[i + 1] === '(' || text[i + 1] === ')')) {
                        highlightedText += text.slice(lastIndex, i) + `<span style="background-color: ${errorColor};">/</span>`;
                        console.error(`Try replacing "${char}" at char ${i} with "\\"`);
                        lastIndex = i + 1;
                        continue;
                    }

                    let color = colors[nestingLevel % colors.length];
                    let uniqueId = generateUniqueId();
                    if (inputEl.highlightGradient === true) {
                        color = `id-${uniqueId}`;
                    }
                    switch(char) {
                        case '(':
                            highlightedText += text.slice(lastIndex, i) + `<span id="${uniqueId}" style="background-color: ${color};">${escapeHtml(char)}`;
                            spanStack.push({ id: uniqueId, start: highlightedText.length, originalSpan: `<span id="${uniqueId}" style="background-color: ${color};">`, nestingLevel });
                            nestingLevel++;
                            lastIndex = i + 1;
                            break;
                        case '<':
                            uniqueId = `${uniqueId}-lora`;
                            color = `id-${uniqueId}`;
                            highlightedText += text.slice(lastIndex, i) + `<span id="${uniqueId}" style="background-color: ${color};">${escapeHtml(char)}`;
                            spanStack.push({ id: uniqueId, start: highlightedText.length - 3, originalSpan: `<span id="${uniqueId}" style="background-color: ${color};">`, nestingLevel });
                            nestingLevel++;
                            lastIndex = i + 1;
                            break;
                        case ')':
                        case '>':
                            if (nestingLevel > 0) {
                                highlightedText += text.slice(lastIndex, i) + `${escapeHtml(char)}</span>`;
                                const { id } = spanStack.pop();
                                nestingLevel--;

                                if (inputEl.highlightGradient === true || id.endsWith('lora')) {
                                    // Check for the strength
                                    const strengthText = text.slice(Math.max(0, i - 10), i);
                                    const match = strengthText.match(/(\d+(\.\d+)?)\s*$/);
                                    if (match) {
                                        const strength = parseFloat(match[1]);
                                        const clampedStrength = Math.max(0, Math.min(2, strength));
                                        const normalizedStrength = clampedStrength / 2;
                                        const newColor = interpolateColor(colors[0], colors[colors.length - 1], easeInOutCubic(normalizedStrength));
                                        uniqueIdMap.set(id, newColor);
                                    }
                                }
                                lastIndex = i + 1;
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
                                const newText = highlightedText.slice(start - (originalSpan.length + 1), highlightedText.length).replace(originalSpan, errorSpanTag);
                                highlightedText = highlightedText.slice(0, start - originalSpan.length + 1) + newText;
                                highlightedText += `</span>`;
                            }
                        }
                    }
                }

                // Apply the updated colors to the highlighted text
                uniqueIdMap.forEach((newColor, id) => {
                    highlightedText = highlightedText.replace(`background-color: id-${id}`, `background-color: ${newColor}`);
                });

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

            nodeType.prototype.onNodeCreated = function () {
                this.populate();
                setTextColors(this.inputEl.inputEl, this.overlayEl);
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
        defaultValue: 'rgba(0, 255, 0, 0.5)\nrgba(0, 0, 255, 0.5)\nrgba(255, 0, 0, 0.5)\nrgba(255, 255, 0, 0.5)',
        attrs: { tooltip: 'A list of either rgb or hex colors, one color per line.' },
    },
    {
        id: 'sn0w.TextboxGradientColors',
        name: '[Sn0w] Custom Textbox Gradient Highlight',
        type: 'boolean',
        defaultValue: false,
        tooltip: 'Makes the textbox highlighting be a gradient between the first and last color based on the strength of the selection.',
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
            });
        },
    };
    app.registerExtension(extension);
};

// Register settings
settingsDefinitions.forEach((setting) => {
    registerSetting(setting);
});
