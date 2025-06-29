import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "sn0w.CustomCharacterNode",
    init() {
        setting = app.ui.settings.addSetting(settingDefinition);
    },
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

            const serializeSubmenus = (submenu, depth = 0) => {
                if (!submenu || !submenu.options) return "";

                const items = submenu.options.map((option) => {
                    const content = typeof option === "string" ? option : option.content;

                    if (option.submenu && option.submenu.options) {
                        const nestedItems = serializeSubmenus(option.submenu, depth + 1);
                        return `${content}::{${nestedItems}}`;
                    }

                    return content;
                });

                return items.join("|");
            };

            const createMenuItem = (content, hasSubmenu = false, submenu = null) => {
                const item = {
                    content: content,
                    disabled: false,
                    callback: newCallback,
                    toString: () => {
                        if (hasSubmenu && submenu && submenu.options) {
                            const serializedSubmenus = serializeSubmenus(submenu);
                            return `${content}::{${serializedSubmenus}}`;
                        }
                        return content;
                    },
                };

                if (hasSubmenu) {
                    item.has_submenu = true;
                    item.submenu = submenu;
                }

                return item;
            };

            const createNestedMenuItems = (data, level = 0) => {
                if (typeof data === "string") {
                    return {
                        content: data,
                        callback: newCallback,
                        toString: () => data,
                    };
                }

                if (Array.isArray(data)) {
                    return data.map((item) => createNestedMenuItems(item, level));
                }

                if (data && typeof data === "object" && data.submenu) {
                    const submenuOptions = createNestedMenuItems(data.submenu, level + 1);
                    return createMenuItem(data.content, true, {
                        options: Array.isArray(submenuOptions) ? submenuOptions : [submenuOptions],
                        callback: newCallback,
                    });
                }

                return data;
            };

            const hierarchicalValues = [createMenuItem("None")];

            Object.keys(seriesGroups).forEach((seriesName) => {
                const submenuOptions = seriesGroups[seriesName].map((characterName) => ({
                    content: characterName,
                    callback: newCallback,
                    toString: () => characterName,
                }));

                hierarchicalValues.push(
                    createMenuItem(seriesName, true, {
                        options: submenuOptions,
                        callback: newCallback,
                    })
                );
            });

            options.callback = undefined;
            existingContextMenu.call(this, hierarchicalValues, options);
        };
    },
});
