import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "sn0w.SimpleSamplerCustom",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "Simple Sampler Custom") {
            const onConnectionsChange = nodeType.prototype.onConnectionsChange;
            nodeType.prototype.onConnectionsChange = function (side, slot, connect, link_info, output) {
                if (slot == 3 || slot == 4) {
                    findInputType(this, slot);
                }
                onConnectionsChange?.apply(side, slot, connect, link_info, output);
            }

            nodeType.prototype.onNodeCreated = function () {
                findInputType(this, 3);
                findInputType(this, 4);
            }

            function findInputType(node, input_id) {
                const input = node.inputs[input_id];
                try {
                    const origin_id = node.graph.links[input.link].origin_id;
                    const link_id = node.graph.links[input.link].id;
                    let input_type;
    
                    // Loop throug all nodes in the workflow until we find the one with the right id and link
                    node.graph._nodes.every(node => {
                        if (node.id == origin_id) {
                            node.outputs.every(output => {
                                output.links.every(link => {
                                    if (link === link_id) {
                                        input_type = output.type;
                                        return false;
                                    }
                                    return true;
                                })
                                return true;
                            });
                        }
                        return true;
                    });
    
                    // Set input dot color to the color of the input type
                    if (input_type == "STRING" || input_type == "CONDITIONING") {
                        node.inputs[input_id].color_on = app.canvas.default_connection_color_byType[input_type];
                    } else {
                        console.error(`The input type has to be STRING or CONDITIONING, it cannot be ${input_type}.`)
                        node.inputs[input_id].color_on = app.canvas.default_connection_color_byType["VAE"];
                    }
                } catch {
                    node.inputs[input_id].color_on = app.canvas.default_connection_color_byType["None"];
                }
            }
        }
    },
});
