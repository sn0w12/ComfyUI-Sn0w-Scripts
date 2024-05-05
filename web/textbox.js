import { app } from "../../../scripts/app.js";
import { api } from '../../scripts/api.js';
import { ComfyWidgets } from "../../../scripts/widgets.js";

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
                // Adding a multiline text widget and storing a reference to the input element
                let textWidget = ComfyWidgets["STRING"](this, "text", ["STRING", { default: "", multiline: true }], app).widget;
                this.inputEl = textWidget.inputEl || textWidget.querySelector('input, textarea');

                // Implement copy functionality with proper callback
                this.addWidget("button", "Copy", "Copy", () => {
                    navigator.clipboard.writeText(this.getTextboxText());
                }, { serialize: false });

                // Implement paste functionality with proper callback handling asynchronous operation
                this.addWidget("button", "Paste", "Paste", () => {
                    navigator.clipboard.readText().then(text => {
                        this.inputEl.value = text;
                    }).catch(error => {
                        console.error('Failed to read clipboard contents:', error);
                    });
                }, { serialize: false });
            };

            nodeType.prototype.onNodeCreated = function () {
                this.populate();
                // Bind the getTextboxText to this instance
                this.getTextboxText = this.getTextboxText.bind(this);

                api.addEventListener('textbox', (event) => {
                    const data = event.detail
                    const outputText = this.getTextboxText();
                    if (this.id == data.id) {
                        api.fetchApi("/textbox_string", {
                            method: "POST",
                            headers: {
                              "Content-Type": "application/json",
                            },
                            body: JSON.stringify(
                                {
                                    node_id: data.id,
                                    outputs: {
                                        output: outputText
                                    }
                                }
                            ),
                        })
                    }
                })
            }
        }
    },
});
