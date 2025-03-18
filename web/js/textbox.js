import { SettingUtils } from "./sn0w.js";
import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

app.registerExtension({
    name: "sn0w.TextboxNode",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "Copy/Paste Textbox") {
            // Get textbox text
            nodeType.prototype.getTextboxText = function () {
                const textbox = this.inputEl ? this.inputEl.value : "";
                return textbox;
            };

            nodeType.prototype.populate = async function () {
                this.inputEl = this.widgets[0];

                // prettier-ignore
                this.addWidget("button", "Copy", "Copy", () => {
                    navigator.clipboard.writeText(this.getTextboxText());
                }, { serialize: false });

                // prettier-ignore
                this.addWidget("button", "Paste", "Paste", () => {
                    navigator.clipboard.readText().then(text => {
                        this.inputEl.value = text;
                        api.dispatchCustomEvent("update_text_highlight");
                    }).catch(error => {
                        console.error('Failed to read clipboard contents:', error);
                    });
                }, { serialize: false });
            };

            nodeType.prototype.onNodeCreated = function () {
                this.populate();
                this.getTextboxText = this.getTextboxText.bind(this);
            };
        }
    },
});
