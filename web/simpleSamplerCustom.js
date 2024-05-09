import { SettingUtils } from './sn0w.js';
import { app } from "../../../scripts/app.js";
import { api } from '../../scripts/api.js';
import { ComfyWidgets } from "../../../scripts/widgets.js";

app.registerExtension({
    name: "sn0w.SimpleSamplerCustom",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "Simple Sampler Custom") {
            const widgets = { // Name: [Type, Default, Min, Max, Snap, Round]
                "polyexponential": {
                    "sigma_max_poly": ["FLOAT", 14.614642, 0.0, 5000.0, 0.01, false],
                    "sigma_min_poly": ["FLOAT", 0.0291675, 0.0, 5000.0, 0.01, false],
                    "rho": ["FLOAT", 1.0, 0.0, 100.0, 0.01, false],
                },
                "vp": { //TODO: fix default values
                    "beta_d": ["FLOAT", 14.0, 0.0, 5000.0, 0.01, false], 
                    "beta_min": ["FLOAT", 0.05, 0.0, 5000.0, 0.01, false],
                    "eps_s": ["FLOAT", 0.075, 0.0, 1.0, 0.0001, false],
                },
                "sigmoid": {
                    "sigma_max_sig": ["FLOAT", 25.0, 0.0, 5000.0, 0.01, false], 
                    "sigma_min_sig": ["FLOAT", 0.0, 0.0, 5000.0, 0.01, false],
                    "steepness": ["FLOAT", 3.5, 0.0, 10.0, 0.01, false],
                    "midpoint_ratio": ["FLOAT", 0.8, 0.0, 1.0, 0.01, false],
                },
            }    

            // Set positive and negative connection colors
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

            nodeType.prototype.onNodeCreated = function () {
                const schedulerWidget = findWidget(this, "scheduler_name");
                console.log(nodeType.prototype)
                schedulerWidget.value = schedulerWidget.value;
            
                // Set up all inputs
                createEverything(this);
                console.log(app)
            
                if (schedulerWidget && schedulerWidget.callback) {
                    const originalCallback = schedulerWidget.callback;
                    schedulerWidget.callback = (newValue) => {
                        setUpCustomInputs(this, newValue);
                        if (originalCallback) originalCallback.call(this, newValue);
                    };
                }

                api.addEventListener('get_scheduler_values', (event) => {
                    const data = event.detail
                    const output = getWidgetOutputs(this, data.widgets_needed);
                    console.log(output)
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
            }

            nodeType.prototype.onConfigure = function () {
                this.serializeCount++;
                const inputName = findWidget(this, "scheduler_name");
                const desiredWidgets = widgets[inputName.value] ? Object.keys(widgets[inputName.value]) : [];
                const removedWidgets = cleanUpInputs(this, desiredWidgets);
                rearrangeWidgets(this, findWidgetIndex(this.widgets, inputName) + 1, 10 - removedWidgets);
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

            function cleanUpInputs(node, desiredWidgets) {
                const widgetsToRemove = createWidgetsToRemove(widgets);
                let widgetsRemoved = 0;

                widgetsToRemove.forEach(widget => {
                    if (!desiredWidgets.includes(widget)) {
                        if (removeWidget(node, widget))
                            widgetsRemoved++;
                    }
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
                
                // Determine which widgets should be present based on inputName
                const desiredWidgets = widgets[inputName] ? Object.keys(widgets[inputName]) : [];
                const existingWidgets = new Set(node.widgets.map(w => w.name));
            
                // Clean up unwanted widgets: remove widgets not in the desired list
                let widgetsRemoved = cleanUpInputs(node, desiredWidgets);
            
                let widgetsAdded = 0;
            
                // Check and add new widgets only if they do not exist
                if (widgets[inputName] !== undefined) {
                    Object.keys(widgets[inputName]).forEach(prop => {
                        // Check if this widget is already added
                        if (!existingWidgets.has(prop)) {
                            const [type, defaultValue, min, max, step, round] = widgets[inputName][prop];
                            if (type === "FLOAT") {
                                let addedWidget = ComfyWidgets[type](node, prop, [type, { default: defaultValue, min: min, max: max, step: step, round: round }], app).widget;
                                console.log(addedWidget)
                                widgetsAdded++;
                            }
                        }
                    });
                }
            
                // Rearrange widgets under 'scheduler_name'
                if (widgetsAdded != 0)
                    rearrangeWidgets(node, findWidgetIndex(node.widgets, findWidget(node, "scheduler_name")) + 1, widgetsAdded);

                let totalWidgets = widgetsAdded - widgetsRemoved;
                console.log(totalWidgets)
            
                // Adjust the size based on widgets added/removed
                node.size[0] = originalWidth;
                node.size[1] = originalHeight + totalWidgets * (70 / 3);
            }
            
            function createEverything(node) {
                Object.keys(widgets).forEach(widget =>
                    Object.keys(widgets[widget]).forEach(prop => {
                        // Check if this widget is already added
                        const [type, defaultValue, min, max, step, round] = widgets[widget][prop];
                        if (type === "FLOAT") {
                            ComfyWidgets[type](node, prop, [type, { default: defaultValue, min: min, max: max, step: step, round: round }], app).widget;
                        }
                    })
                );
            }
        }
    },
});
