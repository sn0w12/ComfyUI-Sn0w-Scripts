import { SettingUtils } from './sn0w.js';
import { app } from "../../../scripts/app.js";

const Id = "sn0w.ExcludedRandomCharacters";
const jsonUrls = ['/extensions/ComfyUI-Sn0w-Scripts/settings/characters.json', '/extensions/ComfyUI-Sn0w-Scripts/settings/custom_characters.json'];

// Function to fetch, sort, and load options from multiple JSON files
const loadOptionsFromJson = async (urls) => {
    const allData = [];

    // Fetch data from each URL and combine it into one array
    for (const url of urls) {
        try {
            const response = await fetch(url);
            if (!response.ok) {
                console.warn('Network response was not ok for URL: ' + url);
                continue;
            }
            const data = await response.json();
            allData.push(...data);
        } catch (error) {
            console.warn('Failed to fetch or parse JSON from URL: ' + url, error);
        }
    }

    if (allData.length === 0) {
        console.error('No data fetched from any URLs');
        return [];
    }

    // Sort the combined data alphabetically by the name property
    const sortedData = allData.sort((a, b) => a.name.localeCompare(b.name));

    // Map the sorted data to the required format
    return sortedData.map(item => ({
        label: item.name,
        value: item.name.replace(/[^a-z0-9]/gi, '_').toLowerCase() // Sanitize the value
    }));
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
