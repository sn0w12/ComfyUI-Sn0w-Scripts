import { SettingUtils } from './sn0w.js';
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

    SettingUtils.setLoggingLevel(loggingArray);
    SettingUtils.logSn0w("Logging Levels Updated", "debug", "setting", `Logging levels selected:\n${loggingArray}`);
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

settingsDefinitions.forEach((setting) => {
    SettingUtils.registerSetting(setting);
});