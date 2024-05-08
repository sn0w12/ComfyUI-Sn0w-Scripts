import { SettingUtils } from './sn0w.js';
import { app } from "../../../scripts/app.js";
import { api } from '../../scripts/api.js';
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
                        setUpCustomInputs(this, newValue);
                    };
                }

                api.addEventListener('get_scheduler_values', (event) => {
                    const data = event.detail
                    const output = getWidgetOutputs(this, 3);
                    if (this.id == data.id) {
                        api.fetchApi(`${SettingUtils.API_PREFIX}/scheduler_values`, {
                            method: "POST",
                            headers: {
                              "Content-Type": "application/json",
                            },
                            body: JSON.stringify(
                                {
                                    node_id: data.id,
                                    outputs: output,
                                }
                            ),
                        })
                    }
                })

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

            function findWidgetIndex(widgets, searchWidget) {
                return widgets.findIndex(widget =>
                    widget.name === searchWidget.name &&
                    widget.value === searchWidget.value &&
                    widget.type === searchWidget.type
                );
            }

            function getWidgetOutputs(node, totalWidgetsToGet) {
                const widgets = node.widgets;
                let startIndex = widgets.length - (totalWidgetsToGet + 3);

            
                if (startIndex < 0) {
                    console.warning("Not enough widgets to move.");
                    return Object.fromEntries(
                        widgets.map(widget => [
                            widget.name, 
                            { value: widget.value }
                        ])
                    );
                }
            
                let outputWidgets = widgets.slice(startIndex, startIndex + totalWidgetsToGet);
            
                return Object.fromEntries(
                    outputWidgets.map(widget => [
                        widget.name, 
                        { value: widget.value }
                    ])
                );
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
                const widgetsToRemove = ["sigma_max", "sigma_min", "rho", "beta_d", "beta_min", "eps_s"];
                let widgetsRemoved = 0;

                widgetsToRemove.forEach(widget => {
                    if (removeWidget(node, widget))
                        widgetsRemoved++;
                });
                return widgetsRemoved;
            }

            function rearrangeWidgets(node, moveWidgetsBehind, totalWidgetsToMove) {
                const widgets = node.widgets;
                // Calculate the starting index for removing the last three widgets
                let startIndex = widgets.length - totalWidgetsToMove;

                // Check if there are at least three widgets to move
                if (startIndex < 0) {
                    console.warning("Not enough widgets to move.");
                    return widgets;
                }

                // Remove the last three widgets from the array
                let widgetsToMove = widgets.splice(startIndex, totalWidgetsToMove);
            
                // Insert them after the widget at index 8
                let newWidgets = [
                    ...widgets.slice(0, moveWidgetsBehind),
                    ...widgetsToMove,
                    ...widgets.slice(moveWidgetsBehind)
                ];
            
                node.widgets = newWidgets;
                return newWidgets;
            }

            function setUpCustomInputs(node, inputName) {
                const originalWidth = node.size[0];
                const originalHeight = node.size[1];
                const widgetsRemoved = cleanUpInputs(node);
                let widgetsAdded = 0;

                const widgets = {
                    "polyexponential": {
                        "sigma_max": ["FLOAT", 14.614642, 0.0, 5000.0, 0.01, false],
                        "sigma_min": ["FLOAT", 0.0291675, 0.0, 5000.0, 0.01, false],
                        "rho": ["FLOAT", 1.0, 0.0, 100.0, 0.01, false],
                    },
                    "vp": { //TODO: fix default values
                        "beta_d": ["FLOAT", 14.0, 0.0, 5000.0, 0.01, false], 
                        "beta_min": ["FLOAT", 0.05, 0.0, 5000.0, 0.01, false],
                        "eps_s": ["FLOAT", 0.075, 0.0, 1.0, 0.0001, false],
                    }
                }

                const widget = widgets[inputName];
                if (widget != undefined) {
                    // Iterate over all widgets to add
                    Object.keys(widget).forEach(prop => {
                        const [type, defaultValue, min, max, step, round] = widget[prop];
                        
                        if (type == "FLOAT") {
                            ComfyWidgets[type](node, prop, [type, { default: defaultValue, min: min, max: max, step: step, round: round }], app).widget;
                            widgetsAdded++;
                        }
                    });
                }

                // Put ne wwidgets under scheduler_name
                rearrangeWidgets(node, findWidgetIndex(node.widgets, findWidget(node, "scheduler_name")) + 1, widgetsAdded)
                let totalWidgets = widgetsAdded - widgetsRemoved;

                // Add or remove height based on widgets added/ removed
                node.size[0] = (originalWidth);
                node.size[1] = (originalHeight + totalWidgets * (70 / 3));
            }
        }
    },
});
