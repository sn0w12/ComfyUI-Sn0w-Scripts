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

            async function setTextColors(inputEl, overlayEl) {
                const customTextboxColors = await SettingUtils.getSetting('sn0w.TextboxColors');
                if (
                    customTextboxColors == null ||
                    (customTextboxColors.length === 1 && customTextboxColors[0] === '') ||
                    customTextboxColors == ''
                ) {
                    inputEl.colors = [
                        'rgba(0, 255, 0, 0.5)',
                        'rgba(0, 0, 255, 0.5)',
                        'rgba(255, 0, 0, 0.5)',
                        'rgba(255, 255, 0, 0.5)',
                    ];
                    syncText(inputEl, overlayEl);
                    return;
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

            async function syncText(inputEl, overlayEl) {
                const text = inputEl.value;
                overlayEl.textContent = text;

                // Colors for nested parentheses
                let colors = inputEl.colors;
                if (colors == undefined) {
                    return;
                }
                let errorColor = inputEl.errorColor;
                if (errorColor == undefined) {
                    return;
                }

                let nestingLevel = 0;
                let highlightedText = '';
                let lastIndex = 0;

                let spanStack = [];

                for (let i = 0; i < text.length; i++) {
                    const char = text[i];

                    // Check for escape character
                    if (char === '\\' && i + 1 < text.length && (text[i + 1] === '(' || text[i + 1] === ')')) {
                        i++;
                        continue;
                    } else if (char === '/' && i + 1 < text.length && (text[i + 1] === '(' || text[i + 1] === ')')) {
                        highlightedText += text.slice(lastIndex, i) + `<span style="background-color: ${errorColor};">/</span>${text[i + 1]}`;
                        console.log(`Try replacing "${char}" at ${i} with "\\"`);
                        i++;
                        lastIndex = i + 1;
                        continue;
                    }

                    switch(char) {
                        case '(':
                            const color = colors[nestingLevel % colors.length];
                            highlightedText += text.slice(lastIndex, i) + `<span style="background-color: ${color};">(`;
                            spanStack.push(highlightedText.length);
                            nestingLevel++;
                            lastIndex = i + 1;
                            break;
                        case ')':
                            nestingLevel--;
                            highlightedText += text.slice(lastIndex, i) + `)</span>`;
                            spanStack.pop();
                            lastIndex = i + 1;
                            break;
                    }
                }

                highlightedText += text.slice(lastIndex);

                if (nestingLevel > 0) {
                    // Apply red highlight to the unclosed spans
                    let insertOffset = 0;
                    while (spanStack.length > 0) {
                        const spanStartIndex = spanStack.pop() - 1;
                        const spanStartTag = `<span style="background-color: ${errorColor};">`;
                        highlightedText =
                            highlightedText.slice(0, spanStartIndex + insertOffset) +
                            spanStartTag +
                            highlightedText.slice(spanStartIndex + insertOffset);
                        insertOffset += spanStartTag.length;
                        highlightedText += `</span>`;
                    }
                }

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
                overlayEl.style.zIndex = '1'; // Ensure it's just below the textarea
                overlayEl.style.pointerEvents = 'none'; // Allow clicks to pass through
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

const id = 'sn0w.TextboxColors';
const settingDefinition = {
    id,
    name: '[Sn0w] Custom Textbox Colors',
    type: SettingUtils.createMultilineSetting,
    defaultValue:
        'rgba(0, 255, 0, 0.5)\nrgba(0, 0, 255, 0.5)\nrgba(255, 0, 0, 0.5)\nrgba(255, 255, 0, 0.5)',
    attrs: { tooltip: 'A list of either rgb or hex colors, one color per line.' },
};

let setting;

const extension = {
    name: id,
    init() {
        setting = app.ui.settings.addSetting(settingDefinition);
    },
};

app.registerExtension(extension);
