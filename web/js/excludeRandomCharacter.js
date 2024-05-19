import { SettingUtils } from './sn0w.js';
import { app } from "../../../scripts/app.js";

const Id = "sn0w.ExcludedRandomCharacters";
const jsonUrl = '/extensions/ComfyUI-Sn0w-Scripts/settings/characters.json';

// Function to fetch, sort, and load options from the JSON file
const loadOptionsFromJson = async (url) => {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();

        // Sort the data alphabetically by the name property
        const sortedData = data.sort((a, b) => a.name.localeCompare(b.name));

        // Map the sorted data to the required format
        return sortedData.map(item => ({
            label: item.name,
            value: item.name.replace(/[^a-z0-9]/gi, '_').toLowerCase() // Sanitize the value
        }));
    } catch (error) {
        console.error('Failed to load options:', error);
        return [];
    }
};

// Function to register the setting
const registerSetting = (settingDefinition) => {
    const extension = {
        name: settingDefinition.id,
        init() {
            app.ui.settings.addSetting(settingDefinition);
        }
    };
    app.registerExtension(extension);
};

// Load options and register the setting
loadOptionsFromJson(jsonUrl).then(options => {
    const SettingDefinition = {
        id: Id,
        name: "[Sn0w] Exclude/Include Random Characters",
        type: SettingUtils.createCheckboxSetting,
        defaultValue: [],
        attrs: {
            options: options,
            tooltip: ""
        }
    };

    registerSetting(SettingDefinition);
}).catch(error => {
    console.error('Error registering setting:', error);
});
