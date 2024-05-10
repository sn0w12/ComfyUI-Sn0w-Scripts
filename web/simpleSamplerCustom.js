import { SettingUtils } from './sn0w.js';
import { widgets } from './settings/scheduler_settings.js';
import { app } from "../../../scripts/app.js";
import { api } from '../../scripts/api.js';
import { ComfyWidgets } from "../../../scripts/widgets.js";

app.registerExtension({
    name: "sn0w.SimpleSamplerCustom",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "Simple Sampler Custom") {
            // Set positive and negative connection colors
            const onConnectInput = nodeType.prototype.onConnectInput;
            nodeType.prototype.onConnectInput = function (targetSlot, type, output, originNode, originSlot) {
                const slot = type[0]
                const inputType = type[1]
                console.log(this)
                console.log(JSON.parse(JSON.stringify(targetSlot.inputs[slot])))

                if (slot == 3 || slot == 4) {
                    if (inputType == "STRING" || inputType == "CONDITIONING") {
                        targetSlot.inputs[slot].color_on = app.canvas.default_connection_color_byType[inputType];
                    } else {
                        console.error(`The input type has to be STRING or CONDITIONING, it cannot be ${inputType}.`)
                        targetSlot.inputs[slot].color_on = app.canvas.default_connection_color_byType["VAE"];
                    }
                }

                onConnectInput?.apply(targetSlot, type, output, originNode, originSlot);
                console.log(targetSlot.inputs[slot])
            }

            nodeType.prototype.onNodeCreated = function () {
                const schedulerWidget = findWidget(this, "scheduler_name");
                schedulerWidget.value = schedulerWidget.value;
            
                // Set up all inputs
                createEverything(this);
                this.inputs[3].type = ["STRING", "CONDITIONING"];
                this.inputs[4].type = ["STRING", "CONDITIONING"];
            
                if (schedulerWidget && schedulerWidget.callback) {
                    const originalCallback = schedulerWidget.callback;
                    schedulerWidget.callback = (newValue) => {
                        showSchedulerInputs(this, newValue);
                        if (originalCallback) originalCallback.call(this, newValue);
                    };
                }

                api.addEventListener('get_scheduler_values', (event) => {
                    const data = event.detail
                    const output = getWidgetOutputs(this, data.widgets_needed);
                    console.log(output);
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

                api.addEventListener('should_decode_image', (event) => {
                    const data = event.detail
                    const output = checkImageOutput(this);
                    console.log(output);
                    if (this.id == data.id) {
                        api.fetchApi(`${SettingUtils.API_PREFIX}/should_decode_image`, {
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
            }

            nodeType.prototype.onConfigure = function () {
                const inputName = findWidget(this, "scheduler_name");
                const desiredWidgets = widgets[inputName.value] ? Object.keys(widgets[inputName.value]) : [];
                showSchedulerInputs(this, inputName, desiredWidgets);
            };            

            function findWidget(node, name) {
                const widget = node.widgets.find(widget => widget.name === name);
                return widget;
            }

            function getWidgetOutputs(node, WidgetsToGet) {
                const widgets = node.widgets;
                
                // Filter out only the widgets that are in the WidgetsToGet array
                const outputWidgets = widgets.filter(widget => WidgetsToGet.includes(widget.name));
                
                // Create an object with the widget names as keys and their values wrapped in an object
                return Object.fromEntries(
                    outputWidgets.map(widget => [
                        widget.name, 
                        { value: widget.value }
                    ])
                );
            }   
            
            function checkImageOutput(node) {
                if (node.outputs[0].links.length === 0)
                    return false;
                return true;
            }

            function createWidgetsToRemove(widgets) {
                // Use a set to avoid duplicates
                const widgetNames = new Set();
            
                // Iterate over each category in the widgets object
                for (const category in widgets) {
                    // Get all keys from the category and add them to the set
                    Object.keys(widgets[category]).forEach(key => widgetNames.add(key));
                }
            
                // Convert the set back to an array
                return Array.from(widgetNames);
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

                let widgetsToMove = widgets.splice(startIndex, totalWidgetsToMove);

                let newWidgets = [
                    ...widgets.slice(0, moveWidgetsBehind),
                    ...widgetsToMove,
                    ...widgets.slice(moveWidgetsBehind)
                ];
            
                node.widgets = newWidgets;
                return newWidgets;
            }
            
            function showSchedulerInputs(node, schedulerName, desiredWidgets = undefined) {
                const originalWidth = node.size[0];
                const originalHeight = node.size[1];
                const originalWidgets = node.widgets;
                const originalWidgetTypes = new Map();
                const resizeNode = !desiredWidgets;
            
                for (const widget of originalWidgets) {
                    originalWidgetTypes.set(widget.name, widget.type);
                }
            
                // Determine which widgets should be present based on schedulerName
                if (!desiredWidgets) {
                    desiredWidgets = widgets[schedulerName] ? new Set(Object.keys(widgets[schedulerName])) : new Set();
                } else {
                    desiredWidgets = new Set(desiredWidgets);
                }
            
                const widgetsToRemove = createWidgetsToRemove(widgets);
            
                for (const widget of widgetsToRemove) {
                    if (!desiredWidgets.has(widget)) {
                        SettingUtils.hideWidget(node, findWidget(node, widget));
                    }
                }
            
                for (const widgetName of desiredWidgets) {
                    const widget = findWidget(node, widgetName);
                    SettingUtils.showWidget(widget);
                    if (widget.type === undefined) {
                        widget.type = originalWidgetTypes.get(widget.name);
                    }
                }
            
                let addedWidgets = 0;
                let removedWidgets = 0;
            
                for (const widget of node.widgets) {
                    if (originalWidgetTypes.get(widget.name) === "converted-widget") {
                        if (widget.type !== "converted-widget")
                            addedWidgets++;
                    } else {
                        if (widget.type === "converted-widget")
                            removedWidgets++;
                    }
                }
            
                // Adjust the size based on widgets added/removed
                if (resizeNode) {
                    node.size[0] = originalWidth;
                    node.size[1] = originalHeight + (addedWidgets - removedWidgets) * (70 / 3);
                }
            }            
            
            function createEverything(node) {
                const allSettings = new Set();
            
                for (const [widgetKey, widgetProps] of Object.entries(widgets)) {
                    for (const [prop, [type, defaultValue, min, max, step, round]] of Object.entries(widgetProps)) {
                        if (type === "FLOAT") {
                            ComfyWidgets[type](node, prop, [type, { default: defaultValue, min: min, max: max, step: step, round: round }], app).widget;
                        }
                        allSettings.add(prop);
                    }
                }

                const originalWidth = node.size[0];
                const originalHeight = node.size[1];
            
                rearrangeWidgets(node, 8, 10);
            
                let nodesHidden = 0;
                for (const widget of node.widgets) {
                    if (allSettings.has(widget.name)) {
                        SettingUtils.hideWidget(node, widget);
                        nodesHidden++;
                    }
                }

                node.size[0] = originalWidth;
                node.size[1] = originalHeight + (-nodesHidden * (70 / 3));
            }            
        }
    },
});
