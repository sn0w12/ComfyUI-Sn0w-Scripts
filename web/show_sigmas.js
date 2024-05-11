import { SettingUtils } from './sn0w.js';
import { app } from "../../../scripts/app.js";
import { api } from '../../scripts/api.js';

app.registerExtension({
    name: "sn0w.ShowSigmas",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "Show Sigmas") {
            // The populate function now returns the Base64 encoded image
            function populate(sigmas) {
                // Define the size of the canvas
                const width = 800;
                const height = 400;

                // Create a canvas element
                const canvas = document.createElement('canvas');
                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext('2d');

                // Background
                ctx.fillStyle = 'white';
                ctx.fillRect(0, 0, width, height);

                // Normalize sigma values to fit within the canvas height
                const maxSigma = Math.max(...sigmas.map(s => s[0]));
                const minSigma = Math.min(...sigmas.map(s => s[0]));
                const range = maxSigma - minSigma;

                // Function to scale a sigma value to the canvas coordinates
                const scaleY = sigma => (height - 20) - (((sigma - minSigma) / range) * (height - 40));
                const scaleX = index => (index / (sigmas.length - 1)) * width;

                // Draw the graph line
                ctx.strokeStyle = 'black';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(scaleX(0), scaleY(sigmas[0][0]));

                sigmas.forEach((sigma, index) => {
                    ctx.lineTo(scaleX(index), scaleY(sigma[0]));
                });

                ctx.stroke();

                // Return the canvas content as a Base64 encoded image
                return canvas.toDataURL('image/png');
            }

            nodeType.prototype.onNodeCreated = function () {
                console.log(this)
                api.addEventListener('sn0w_get_sigmas', (event) => {
                    const data = event.detail;
                    console.log(`Recieved ${data}`);
                    if (this.id == data.id) {
                        console.log(`Recieved ${data.sigmas}`);
                        const imageBase64 = populate(data.sigmas);

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
