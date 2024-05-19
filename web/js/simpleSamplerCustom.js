import { SettingUtils } from './sn0w.js';
import { widgets } from '../settings/scheduler_settings.js';
import { app } from "../../../scripts/app.js";
import { api } from '../../../scripts/api.js';
import { ComfyWidgets } from "../../../scripts/widgets.js";

app.registerExtension({
    name: "sn0w.SimpleSamplerCustom",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        const allSettings = new Set();

        if (nodeData.name === "Simple Sampler Custom") {
            // Set positive and negative connection colors
            const onConnectInput = nodeType.prototype.onConnectInput;
            nodeType.prototype.onConnectInput = function (targetSlot, type, output, originNode, originSlot) {
                const slot = type[0]
                const inputType = type[1]

                const initialCount = countWidgetsOfType(targetSlot.widgets, "converted-widget");
                const originalSize = [targetSlot.size[0], targetSlot.size[1]];

                if (slot === 3 || slot === 4) {
                    if (inputType == "STRING" || inputType == "CONDITIONING") {
                        targetSlot.inputs[slot].color_on = app.canvas.default_connection_color_byType[inputType];
                    } else {
                        console.error(`The input type has to be STRING or CONDITIONING, it cannot be ${inputType}.`)
                        targetSlot.inputs[slot].color_on = app.canvas.default_connection_color_byType["VAE"];
                    }
                } else if (slot === 5) {
                    hideAllSchedulerWidgets(targetSlot);
                    SettingUtils.hideWidget(targetSlot, findWidget(targetSlot, "scheduler_name"));

                    resizeNode(targetSlot, initialCount, originalSize);
                } else if (slot === 6) {
                    hideAllLatentWidgets(targetSlot);
                    resizeNode(targetSlot, initialCount, originalSize);
                }

                onConnectInput?.apply(targetSlot, type, output, originNode, originSlot);
            }

            // Handle when connection is disconnected
            const onConnectionsChange = nodeType.prototype.onConnectionsChange;
            nodeType.prototype.onConnectionsChange = function (side, slot, connect, link_info, output) {
                if (slot === 5) {
                    if (this.inputs[slot].link === null) {
                        const initialCount = countWidgetsOfType(this.widgets, "converted-widget");
                        const originalSize = [this.size[0], this.size[1]];

                        const schedulerWidget = findWidget(this, "scheduler_name");
                        showSchedulerInputs(this, schedulerWidget.value);
                        SettingUtils.showWidget(schedulerWidget);
                        if (schedulerWidget.type === undefined)
                            schedulerWidget.type = "combo";

                        resizeNode(this, initialCount, originalSize);
                    }
                } else if (slot === 6) {
                    const initialCount = countWidgetsOfType(this.widgets, "converted-widget");
                    const originalSize = [this.size[0], this.size[1]];

                    if (this.inputs[slot].link === null)
                        showAllLatentWidgets(this);

                    resizeNode(this, initialCount, originalSize);
                }
                onConnectionsChange?.apply(side, slot, connect, link_info, output);
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

                api.addEventListener('sampler_get_sigmas', (event) => {
                    const data = event.detail;
                    if (this.id == data.id) {
                        const imageBase64 = SettingUtils.drawSigmas(data.sigmas);

                        // Send the generated image data back to the server
                        api.fetchApi(`${SettingUtils.API_PREFIX}/get_sigmas`, {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json",
                            },
                            body: JSON.stringify(
                                {
                                    node_id: data.id,
                                    outputs: {
                                        output: imageBase64
                                    }
                                }
                            ),
                        })
                    }
                });
            }

            nodeType.prototype.onConfigure = function () {
                const inputName = findWidget(this, "scheduler_name");
                const desiredWidgets = widgets[inputName.value] ? Object.keys(widgets[inputName.value]) : [];
                showSchedulerInputs(this, inputName, desiredWidgets);


                if (this.inputs[5].link !== null) {
                    hideAllSchedulerWidgets(this);
                    SettingUtils.hideWidget(this, findWidget(this, "scheduler_name"));
                }
                if (this.inputs[6].link !== null) {
                    hideAllLatentWidgets(this);
                }
            };            

            function findWidget(node, name) {
                const widget = node.widgets.find(widget => widget.name === name);
                return widget;
            }

            function countWidgetsOfType(widgets, type) {
                return widgets.filter(widget => widget.type === type).length;
            }

            function resizeNode(node, initialCount, originalSize) {
                const finalCount = countWidgetsOfType(node.widgets, "converted-widget");
                node.size[0] = originalSize[0];
                node.size[1] = originalSize[1] + (initialCount - finalCount) * (70 / 3);
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
                try {
                    if (node.outputs[0].links.length === 0)
                        return false;
                    return true;
                } catch {
                    return false;
                }
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
                let widgets = node.widgets;
            
                // Calculate the starting index for removing the last N widgets
                let startIndex = widgets.length - totalWidgetsToMove;
            
                // Check if there are enough widgets to move
                if (startIndex < 0) {
                    console.warning("Not enough widgets to move.");
                    return widgets;
                }
            
                // Extract the last N widgets to be moved
                let widgetsToMove = widgets.splice(startIndex, totalWidgetsToMove);
                
                // Find the scheduler widget and ensure it is not duplicated
                const schedulerWidget = findWidget(node, "scheduler_name");
                
                // If the schedulerWidget is found, remove existing occurrences from the current widgets array
                if (schedulerWidget) {
                    widgets = widgets.filter(widget => widget !== schedulerWidget);
                }
            
                // Ensure the insertion index is within the bounds of the current array
                moveWidgetsBehind = Math.max(0, Math.min(moveWidgetsBehind, widgets.length));
            
                // Prepare the new widgets array by inserting schedulerWidget followed by widgetsToMove
                let newWidgets = [
                    ...widgets.slice(0, moveWidgetsBehind),
                    schedulerWidget,
                    ...widgetsToMove,
                    ...widgets.slice(moveWidgetsBehind)
                ];
            
                // Update the node's widgets with the newly ordered widgets
                node.widgets = newWidgets;
                
                return newWidgets;
            }
            
            function showSchedulerInputs(node, schedulerName, desiredWidgets = undefined) {
                const shouldResizeNode = !desiredWidgets;
                const initialCount = countWidgetsOfType(node.widgets, "converted-widget");
                const originalSize = [node.size[0], node.size[1]];
                const originalWidgetTypes = new Map();
            
                for (const widget of node.widgets) {
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
                if (shouldResizeNode) {
                    resizeNode(node, initialCount, originalSize);
                }
            }    
            
            function hideAllSchedulerWidgets(node) {
                let nodesHidden = 0;
                for (const widget of node.widgets) {
                    if (allSettings.has(widget.name)) {
                        SettingUtils.hideWidget(node, widget);
                        nodesHidden++;
                    }
                }
                return nodesHidden;
            }

            function hideAllLatentWidgets(node) {
                let heightWidget = findWidget(node, "height");
                let widthWidget = findWidget(node, "width");

                SettingUtils.hideWidget(node, heightWidget);
                SettingUtils.hideWidget(node, widthWidget);

                // Remove inputs if they are there
                if (node.inputs.some(obj => obj.name === "width")) {
                    node.inputs = node.inputs.filter(obj => obj.name !== "width");
                }
                if (node.inputs.some(obj => obj.name === "height")) {
                    node.inputs = node.inputs.filter(obj => obj.name !== "height");
                }
            }

            function showAllLatentWidgets(node) {
                let heightWidget = findWidget(node, "height");
                let widthWidget = findWidget(node, "width");
                
                // Check if the height or width is an input instead of a widget
                if (!node.inputs.some(obj => obj.name === "width")) {
                    SettingUtils.showWidget(widthWidget);
                    if (widthWidget.type === undefined)
                        widthWidget.type = "number";
                }
                if (!node.inputs.some(obj => obj.name === "height")) {
                    SettingUtils.showWidget(heightWidget);
                    if (heightWidget.type === undefined)
                        heightWidget.type = "number";
                }
            }
            
            function createEverything(node) {
                for (const [widgetKey, widgetProps] of Object.entries(widgets)) {
                    for (const [prop, [type, defaultValue, min, max, step, round]] of Object.entries(widgetProps)) {
                        if (type === "FLOAT") {
                            ComfyWidgets[type](node, prop, [type, { default: defaultValue, min: min, max: max, step: step, round: round }], app).widget;
                        }
                        allSettings.add(prop);
                    }
                }

                const originalSize = [node.size[0], node.size[1]];
            
                rearrangeWidgets(node, 7, allSettings.size);
                const nodesHidden = hideAllSchedulerWidgets(node);

                node.size[0] = originalSize[0];
                node.size[1] = originalSize[1] + (-nodesHidden * (70 / 3));
            }            
        }
    },
});
