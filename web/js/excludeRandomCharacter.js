import { SettingUtils } from './sn0w.js';
import { app } from "../../../scripts/app.js";

const Id = "sn0w.ExcludedRandomCharacters";
const jsonUrls = ['/extensions/ComfyUI-Sn0w-Scripts/settings/characters.json', '/extensions/ComfyUI-Sn0w-Scripts/settings/custom_characters.json'];

// Function to fetch, sort, and load options from multiple JSON files
const loadOptionsFromJson = async (urls) => {
    try {
        const allData = [];
        
        // Fetch data from each URL and combine it into one array
        for (const url of urls) {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error('Network response was not ok for URL: ' + url);
            }
            const data = await response.json();
            allData.push(...data);
        }

        // Sort the combined data alphabetically by the name property
        const sortedData = allData.sort((a, b) => a.name.localeCompare(b.name));

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
loadOptionsFromJson(jsonUrls).then(options => {
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
