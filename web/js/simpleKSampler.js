import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "sn0w.SimpleKSampler",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "Sn0w KSampler") {
            nodeType.prototype.onNodeCreated = function () {
                this.inputs[3].type = "*";
                this.inputs[4].type = "*";
            };

            nodeType.prototype.onConfigure = function () {
                this.inputs[3].type = "*";
                this.inputs[4].type = "*";
            };
        }
    },
});
