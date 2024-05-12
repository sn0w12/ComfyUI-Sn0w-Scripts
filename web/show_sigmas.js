import { SettingUtils } from './sn0w.js';
import { app } from "../../../scripts/app.js";
import { api } from '../../scripts/api.js';

app.registerExtension({
    name: "sn0w.ShowSigmas",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "Show Sigmas") {
            nodeType.prototype.onNodeCreated = function () {
                api.addEventListener('sn0w_get_sigmas', (event) => {
                    const data = event.detail;
                    console.log(`Recieved ${data}`);
                    if (this.id == data.id) {
                        console.log(`Recieved ${data.sigmas}`);
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
            };
        }
    },
});
