"""
Support for eQ-3 Bluetooth Smart thermostats.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/climate.eq3btsmart/
"""
import logging

import voluptuous as vol

from homeassistant.components.climate import ClimateDevice, PLATFORM_SCHEMA, \
    STATE_AUTO
from homeassistant.const import (
    CONF_MAC, TEMP_CELSIUS, CONF_DEVICES, ATTR_TEMPERATURE)
from homeassistant.util.temperature import convert
import homeassistant.helpers.config_validation as cv

from bluepy_devices.devices.eq3btsmart import EQ3BTSMART_AUTO, \
    EQ3BTSMART_MANUAL, EQ3BTSMART_BOOST, EQ3BTSMART_AWAY, EQ3BTSMART_CLOSED, \
    EQ3BTSMART_OPEN

REQUIREMENTS = ['bluepy_devices==0.3.0']

_LOGGER = logging.getLogger(__name__)

EQ3BT_ATTR_MODE = 'mode'
EQ3BT_ATTR_MODE_READABLE = 'mode_readable'
EQ3BT_ATTR_VALVE_STATE = 'Valve'
EQ3BT_ATTR_LOCKED = 'Locked'
EQ3BT_ATTR_WINDOW = 'WindowOpen'
EQ3BT_ATTR_BATTERY = 'LowBattery'

DEVICE_SCHEMA = vol.Schema({
    vol.Required(CONF_MAC): cv.string,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DEVICES):
        vol.Schema({cv.string: DEVICE_SCHEMA}),
})


STATE_MANUAL = "Manual"
STATE_BOOST = "Boost"
STATE_AWAY = "Away"
STATE_CLOSED = "Off"
STATE_OPEN = "On"

EQ3BT_STATE_MAP = {
    EQ3BTSMART_AUTO: STATE_AUTO,
    EQ3BTSMART_MANUAL: STATE_MANUAL,
    EQ3BTSMART_BOOST: STATE_BOOST,
    EQ3BTSMART_AWAY: STATE_AWAY,
    EQ3BTSMART_CLOSED: STATE_CLOSED,
    EQ3BTSMART_OPEN: STATE_OPEN,
}


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the eQ-3 BLE thermostats."""
    devices = []

    for name, device_cfg in config[CONF_DEVICES].items():
        mac = device_cfg[CONF_MAC]
        devices.append(EQ3BTSmartThermostat(mac, name))

    add_devices(devices)


# pylint: disable=import-error
class EQ3BTSmartThermostat(ClimateDevice):
    """Representation of a eQ-3 Bluetooth Smart thermostat."""

    def __init__(self, _mac, _name):
        """Initialize the thermostat."""
        from bluepy_devices.devices import eq3btsmart

        self._name = _name
        self._thermostat = eq3btsmart.EQ3BTSmartThermostat(_mac)
        self._away = None

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement that is used."""
        return TEMP_CELSIUS

    @property
    def current_operation(self):
        """Return current operation ie. auto, manual, boost, away."""
        return EQ3BT_STATE_MAP[self._thermostat.mode]

    def set_operation_mode(self, operation_mode):
        """Set new target operation mode."""
        for mode, op_mode in EQ3BT_STATE_MAP.items():
            if op_mode == operation_mode:
                self._thermostat.mode = mode
                break

    @property
    def operation_list(self):
        """List of available operation modes."""
        op_list = [STATE_AUTO, STATE_MANUAL, STATE_BOOST,
                   STATE_CLOSED, STATE_OPEN]
        return op_list

    @property
    def current_temperature(self):
        """Can not report temperature, so return target_temperature."""
        return self.target_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._thermostat.target_temperature

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        self._thermostat.target_temperature = temperature

    @property
    def device_state_attributes(self):
        """Return the device specific state attributes."""
        return {
            EQ3BT_ATTR_MODE: self._thermostat.mode,
            EQ3BT_ATTR_MODE_READABLE: self._thermostat.mode_readable,
            EQ3BT_ATTR_VALVE_STATE: self._thermostat.valve_state,
            EQ3BT_ATTR_LOCKED: self._thermostat.locked,
            EQ3BT_ATTR_WINDOW: self._thermostat.window_open,
            EQ3BT_ATTR_BATTERY: self._thermostat.low_battery,
        }

    @property
    def is_away_mode_on(self):
        """Return if away mode is on."""
        return self._away

    def turn_away_mode_on(self):
        """Turn away on."""
        self._thermostat.mode = EQ3BTSMART_AWAY
        self._away = True

    def turn_away_mode_off(self):
        """Turn away off."""
        self._thermostat.mode = EQ3BTSMART_AUTO
        self._away = False

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return convert(self._thermostat.min_temp, TEMP_CELSIUS,
                       self.unit_of_measurement)

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return convert(self._thermostat.max_temp, TEMP_CELSIUS,
                       self.unit_of_measurement)

    def update(self):
        """Update the data from the thermostat."""
        self._thermostat.update()
        self._away = self._thermostat.mode == EQ3BTSMART_AWAY
