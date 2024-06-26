import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "sn0w.SimpleKSampler",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "Simple KSampler") {
            const onConnectInput = nodeType.prototype.onConnectInput;
            nodeType.prototype.onConnectInput = function (targetSlot, type, output, originNode, originSlot) {
                if (targetSlot === 3 || targetSlot === 4) {
                    if (type == "STRING" || type == "CONDITIONING") {
                        this.inputs[targetSlot].color_on = app.canvas.default_connection_color_byType[type];
                    } else {
                        console.error(`The input type has to be STRING or CONDITIONING, it cannot be ${type}.`)
                        this.inputs[targetSlot].color_on = app.canvas.default_connection_color_byType["VAE"];
                    }
                }

                onConnectInput.apply(this, arguments);
            }

            nodeType.prototype.onNodeCreated = function () {
                this.inputs[3].type = ["STRING", "CONDITIONING"];
                this.inputs[4].type = ["STRING", "CONDITIONING"];
            }

            nodeType.prototype.onConfigure = function () {
                this.inputs[3].type = ["STRING", "CONDITIONING"];
                this.inputs[4].type = ["STRING", "CONDITIONING"];
            }
        }
    }
});