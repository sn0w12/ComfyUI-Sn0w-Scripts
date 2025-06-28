import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "sn0w.CustomCharacterNode",
    async setup() {
        const existingContextMenu = LiteGraph.ContextMenu;
        LiteGraph.ContextMenu = function (values, options) {
            if (values[values.length - 1] != "SN0W_CHARACTER_SELECTOR") {
                return existingContextMenu.call(this, values, options);
            }

            const originalCallback = options.callback;
            const seriesGroups = {};
            values.slice(1).forEach((value) => {
                const match = value.match(/^(.+?)\s*\((.+?)\)$/);
                if (match) {
                    const [, , seriesName] = match;
                    if (!seriesGroups[seriesName]) {
                        seriesGroups[seriesName] = [];
                    }
                    seriesGroups[seriesName].push(value);
                }
            });

            const newCallback = (item, options) => {
                if (originalCallback && item && item.content) {
                    originalCallback(item.content, options);
                }
            };

            const hierarchicalValues = [{ content: "None", disabled: false, callback: newCallback }];
            Object.keys(seriesGroups).forEach((seriesName) => {
                hierarchicalValues.push({
                    content: seriesName,
                    disabled: false,
                    has_submenu: true,
                    submenu: {
                        options: seriesGroups[seriesName].map((characterName) => ({
                            content: characterName,
                            callback: newCallback,
                        })),
                    },
                });
            });

            options.callback = undefined;
            existingContextMenu.call(this, hierarchicalValues, options);
        };
    },
});
