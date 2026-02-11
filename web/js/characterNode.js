import { app } from "../../../scripts/app.js";
import { $el } from "../../../../../../../../../../../../../../../../scripts/ui.js";

const linkSetting = (name, setter, value, attrs) => {
    const link = $el("a", {
        href: attrs.href || "#",
        target: attrs.target || "_blank",
        textContent: attrs.text || "Open Link",
        style: {
            color: "#007bff",
            textDecoration: "underline",
            cursor: "pointer",
            display: "block",
            padding: "8px 0",
        },
    });

    return link;
};

app.registerExtension({
    name: "sn0w.CustomCharacterNode",
    init() {
        app.ui.settings.addSetting({
            id: "sn0w.CharacterSettings.ManageVisibleSeries",
            name: "Manage Visible Series",
            type: linkSetting,
            attrs: {
                href: "/sn0w/series_selector",
                target: "_blank",
                text: "Manage Visible Series",
            },
        });
    },
    async setup() {
        const existingContextMenu = LiteGraph.ContextMenu;
        LiteGraph.ContextMenu = function (values, options) {
            if (values[values.length - 1] != "SN0W_CHARACTER_SELECTOR") {
                return existingContextMenu.call(this, values, options);
            }

            const originalCallback = options.callback;
            const newCallback = (item, options) => {
                if (originalCallback && item) {
                    originalCallback(item.content, options);
                }
            };

            // Pre-define toString functions to avoid creating closures in loops
            const simpleToString = function () {
                return this.content;
            };
            const submenuToString = function () {
                if (this.submenu && this.submenu.options) {
                    const parts = [];
                    for (let i = 0; i < this.submenu.options.length; i++) {
                        parts.push(this.submenu.options[i].toString());
                    }
                    return `${this.content}::{${parts.join("|")}}`;
                }
                return this.content;
            };

            // Build tree structure (optimized with direct property access)
            const menuTree = {};
            for (let i = 1; i < values.length; i++) {
                const parts = values[i].split("|");
                let current = menuTree;
                const lastIdx = parts.length - 1;

                for (let j = 0; j < lastIdx; j++) {
                    const part = parts[j];
                    if (!current[part]) {
                        current[part] = {};
                    }
                    current = current[part];
                }
                if (values[i] === "SN0W_CHARACTER_SELECTOR") {
                    continue; // Skip the special identifier
                }
                current[parts[lastIdx]] = values[i];
            }

            // Build menu items recursively
            const buildMenu = (tree, depth) => {
                const keys = Object.keys(tree).sort();
                const items = new Array(keys.length);

                for (let i = 0; i < keys.length; i++) {
                    const key = keys[i];
                    const sub = tree[key];

                    if (typeof sub === "string") {
                        // Leaf node - extract last part directly
                        const lastPipeIdx = sub.lastIndexOf("|");
                        const lastPart = lastPipeIdx >= 0 ? sub.substring(lastPipeIdx + 1) : sub;

                        items[i] = {
                            content: lastPart,
                            disabled: false,
                            callback: newCallback,
                            toString: simpleToString,
                        };
                    } else {
                        // Submenu node
                        const keyItem = {
                            content: key,
                            disabled: false,
                            callback: newCallback,
                            toString: simpleToString,
                        };
                        const submenu = {
                            options: buildMenu(sub, depth + 1),
                        };
                        if (depth > 0) {
                            submenu.options.unshift(keyItem);
                        }

                        items[i] = {
                            content: key,
                            disabled: false,
                            has_submenu: true,
                            submenu: submenu,
                            toString: submenuToString,
                        };
                    }
                }
                return items;
            };

            const noneItem = {
                content: "None",
                disabled: false,
                toString: simpleToString,
            };

            const hierarchicalValues = [noneItem].concat(buildMenu(menuTree, 0));

            options.callback = undefined;
            existingContextMenu.call(this, hierarchicalValues, options);
        };
    },
});
