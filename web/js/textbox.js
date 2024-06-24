import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "sn0w.Textbox",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "Copy/Paste Textbox") {
            // Get textbox text
            nodeType.prototype.getTextboxText = function() {
                const textbox = this.inputEl ? this.inputEl.value : '';
                return textbox;
            };

            nodeType.prototype.populate = function() {
                this.inputEl = this.widgets[0];

                this.addWidget("button", "Copy", "Copy", () => {
                    navigator.clipboard.writeText(this.getTextboxText());
                }, { serialize: false });

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
                    this.inputEl.inputEl.parentNode.insertBefore(this.overlayEl, this.inputEl.inputEl);

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
                        childList: true
                    });

                    this.inputEl.inputEl.addEventListener('keydown', (event) => {
                        if (event.ctrlKey && (event.key === 'ArrowUp' || event.key === 'ArrowDown')) {
                            setTimeout(() => {
                                syncText(this.inputEl, this.overlayEl);
                            }, 10);
                        }
                    });    

                    setTimeout(() => {
                        syncText(this.inputEl, this.overlayEl);
                        setOverlayPosition(this.inputEl, this.overlayEl);
                        setOverlayStyle(this.inputEl, this.overlayEl);
                    }, 10);  
                } else {
                    console.error('Parent node of input element is not available.');
                }
            };

            function syncText(inputEl, overlayEl) {
                const text = inputEl.value;
                overlayEl.textContent = text;
            
                // Apply styles directly
                overlayEl.style.color = 'transparent';
                overlayEl.style.overflow = 'hidden';
                overlayEl.style.whiteSpace = 'pre-wrap';
                overlayEl.style.wordWrap = 'break-word';
            
                // Colors for nested parentheses
                const colors = ['rgba(0, 255, 0, 0.5)', 'rgba(0, 0, 255, 0.5)', 'rgba(255, 0, 0, 0.5)', 'rgba(255, 255, 0, 0.5)'];
            
                let nestingLevel = 0;
                let highlightedText = '';
                let lastIndex = 0;
            
                const regex = /(\()|(\))/g;
                let match;
                while ((match = regex.exec(text)) !== null) {
                    if (match[0] === '(') {
                        const color = colors[nestingLevel % colors.length];
                        nestingLevel++;
                        highlightedText += text.slice(lastIndex, match.index) + `<span style="background-color: ${color};">${match[0]}`;
                    } else if (match[0] === ')') {
                        nestingLevel--;
                        const color = colors[nestingLevel % colors.length];
                        highlightedText += text.slice(lastIndex, match.index) + `${match[0]}</span>`;
                    }
                    lastIndex = regex.lastIndex;
                }
                highlightedText += text.slice(lastIndex);
            
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
            }

            nodeType.prototype.onNodeCreated = function () {
                this.populate();
                this.getTextboxText = this.getTextboxText.bind(this);
            }
        }
    },
});
