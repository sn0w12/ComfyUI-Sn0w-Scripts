import { app } from "../../../scripts/app.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";

app.registerExtension({
    name: "sn0w.SimpleSamplerCustom",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "Simple Sampler Custom") {
            const onConnectInput = nodeType.prototype.onConnectInput;
            nodeType.prototype.onConnectInput = function (targetSlot, type, output, originNode, originSlot) {
                const slot = type[0]
                const inputType = type[1]

                if (slot == 3 || slot == 4) {
                    if (inputType == "STRING" || inputType == "CONDITIONING") {
                        targetSlot.inputs[slot].color_on = app.canvas.default_connection_color_byType[inputType];
                    } else {
                        console.error(`The input type has to be STRING or CONDITIONING, it cannot be ${inputType}.`)
                        targetSlot.inputs[slot].color_on = app.canvas.default_connection_color_byType["VAE"];
                    }
                }

                onConnectInput?.apply(targetSlot, type, output, originNode, originSlot);
            }

            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const schedulerWidget = findWidget(this, "scheduler_name");

                if (schedulerWidget && schedulerWidget.callback) {
                    schedulerWidget.callback = (newValue) => {
                        console.log("Scheduler value changed to:", newValue);
                        setUpCustomInputs(this, newValue);
                    };
                }

                onNodeCreated?.apply()
            }

            nodeType.prototype.onConfigure = function () {
                const scheduler = findWidget(this, "scheduler_name");
                setUpCustomInputs(this, scheduler.value);
            }

            function findWidget(node, name) {
                const widget = node.widgets.find(widget => widget.name === name);
                return widget;
            }            

            function removeWidget(node, widgetName) {
                const w = node.widgets?.findIndex((w) => w.name === widgetName);
                if (w>=0) {
                    node.widgets.splice(w, 1);
                    node.size = node.computeSize();
                    return true;
                }
                return false
            }

            function cleanUpInputs(node) {
                const widgetsToRemove = ["sigma_max", "sigma_min", "rho"];
                let widgetsRemoved = 0;

                widgetsToRemove.forEach(widget => {
                    if (removeWidget(node, widget))
                        widgetsRemoved++;
                });
                return widgetsRemoved;
            }

            function setUpCustomInputs(node, inputName) {
                const originalWidth = node.size[0];
                const originalHeight = node.size[1];
                const widgetsRemoved = cleanUpInputs(node);
                let widgetsAdded = 0;

                if (inputName === "polyexponential") {
                    ComfyWidgets["FLOAT"](node, "sigma_max", ["FLOAT", { default: 14.614642, min: 0.0, max: 5000.0, step:0.01, round: false }], app).widget;
                    ComfyWidgets["FLOAT"](node, "sigma_min", ["FLOAT", { default: 0.0291675, min: 0.0, max: 5000.0, step:0.01, round: false }], app).widget;
                    ComfyWidgets["FLOAT"](node, "rho", ["FLOAT", { default: 1.0, min: 0.0, max: 100.0, step:0.01, round: false }], app).widget;
                    widgetsAdded = 3;
                }

                let totalWidgets = widgetsAdded - widgetsRemoved;

                node.size[0] = (originalWidth);
                node.size[1] = (originalHeight + totalWidgets * (70 / 3));
            }
        }
    },
});
