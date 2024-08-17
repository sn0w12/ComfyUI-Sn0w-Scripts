import { SettingUtils } from './sn0w.js';
import { app } from '../../../scripts/app.js';
import { api } from '../../../scripts/api.js';

async function updateLoggingLevel() {
    const settingsArray = settingsDefinitions.map(setting => ({
        url: setting.id,
        defaultValue: setting.defaultValue,
    }));
    const settings = await SettingUtils.getMultipleSettings(settingsArray);

    let loggingArray = []
    settingsArray.forEach(setting => {
        const settingValueArr = setting.url.split(".");
        const settingValue = settingValueArr[settingValueArr.length - 1].toUpperCase();
        if (settings[setting.url] == true) {
            loggingArray.push(settingValue);
        }
    });
    await api.storeSetting("sn0w.LoggingLevel", loggingArray)

    await api.fetchApi(`${SettingUtils.API_PREFIX}/update_logging_level`, {
        method: 'GET',
    });
    SettingUtils.logSn0w(`Logging levels selected:\n${await SettingUtils.getSetting("sn0w.LoggingLevel")}`, "debug")
}

const debouncedUpdateLoggingLevel = SettingUtils.debounce(updateLoggingLevel, 1000);

const settingsDefinitions = [
    {
        id: 'sn0w.LoggingLevel.Debug',
        name: 'Debug',
        defaultValue: false,
        type: 'boolean',
        onChange: debouncedUpdateLoggingLevel,
    },
    {
        id: 'sn0w.LoggingLevel.Informational',
        name: 'Informational',
        defaultValue: true,
        type: 'boolean',
        onChange: debouncedUpdateLoggingLevel,
    },
    {
        id: 'sn0w.LoggingLevel.Warning',
        name: 'Warning',
        defaultValue: true,
        type: 'boolean',
        onChange: debouncedUpdateLoggingLevel,
    },
]

const registerSetting = (settingDefinition) => {
    const extension = {
        name: settingDefinition.id,
        init() {
            const setting = app.ui.settings.addSetting({
                id: settingDefinition.id,
                name: settingDefinition.name,
                type: settingDefinition.type,
                defaultValue: settingDefinition.defaultValue,
                attrs: settingDefinition.attrs,
                options: settingDefinition.options,
                onChange: settingDefinition.onChange,
            });
        },
    };
    app.registerExtension(extension);
};

settingsDefinitions.forEach((setting) => {
    registerSetting(setting);
});