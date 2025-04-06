"""Sensor platform for RDW Vehicle Information."""
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE, UnitOfMass, UnitOfLength, UnitOfSpeed, EntityCategory
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util.dt import parse_datetime # For parsing date strings

from .const import DOMAIN, CONF_SENSORS, RDW_API_KEYS
from .coordinator import RdwDataUpdateCoordinator
from .entity import RdwEntity

_LOGGER = logging.getLogger(__name__)

# Define mappings for specific keys to device class, unit, etc.
# Enhance this map based on the specific data types and units RDW provides
SENSOR_DESCRIPTIONS: dict[str, dict] = {
    "vervaldatum_apk_dt": {"device_class": SensorDeviceClass.DATE},
    "datum_tenaamstelling_dt": {"device_class": SensorDeviceClass.DATE},
    "datum_eerste_toelating_dt": {"device_class": SensorDeviceClass.DATE},
    "datum_eerste_tenaamstelling_in_nederland_dt": {"device_class": SensorDeviceClass.DATE},
    "massa_ledig_voertuig": {"native_unit_of_measurement": UnitOfMass.KILOGRAMS, "state_class": SensorStateClass.MEASUREMENT, "icon": "mdi:weight-kilogram"},
    "toegestane_maximum_massa_voertuig": {"native_unit_of_measurement": UnitOfMass.KILOGRAMS, "state_class": SensorStateClass.MEASUREMENT, "icon": "mdi:weight-kilogram"},
    "massa_rijklaar": {"native_unit_of_measurement": UnitOfMass.KILOGRAMS, "state_class": SensorStateClass.MEASUREMENT, "icon": "mdi:weight-kilogram"},
    "maximum_massa_trekken_ongeremd": {"native_unit_of_measurement": UnitOfMass.KILOGRAMS, "state_class": SensorStateClass.MEASUREMENT, "icon": "mdi:weight-kilogram"},
    "maximum_trekken_massa_geremd": {"native_unit_of_measurement": UnitOfMass.KILOGRAMS, "state_class": SensorStateClass.MEASUREMENT, "icon": "mdi:weight-kilogram"},
    "cilinderinhoud": {"native_unit_of_measurement": "cm³", "state_class": SensorStateClass.MEASUREMENT, "icon": "mdi:engine"},
    "lengte": {"native_unit_of_measurement": UnitOfLength.CENTIMETERS, "state_class": SensorStateClass.MEASUREMENT, "icon": "mdi:arrow-left-right-bold"},
    "breedte": {"native_unit_of_measurement": UnitOfLength.CENTIMETERS, "state_class": SensorStateClass.MEASUREMENT, "icon": "mdi:arrow-expand-horizontal"},
    "hoogte_voertuig": {"native_unit_of_measurement": UnitOfLength.CENTIMETERS, "state_class": SensorStateClass.MEASUREMENT, "icon": "mdi:arrow-up-down-bold"},
    "wielbasis": {"native_unit_of_measurement": UnitOfLength.CENTIMETERS, "state_class": SensorStateClass.MEASUREMENT, "icon": "mdi:car-cog"},
    "maximale_constructiesnelheid": {"native_unit_of_measurement": UnitOfSpeed.KILOMETERS_PER_HOUR, "state_class": SensorStateClass.MEASUREMENT, "icon": "mdi:speedometer"},
    "catalogusprijs": {"native_unit_of_measurement": "EUR", "device_class": SensorDeviceClass.MONETARY, "icon": "mdi:currency-eur"},
    "bruto_bpm": {"native_unit_of_measurement": "EUR", "device_class": SensorDeviceClass.MONETARY, "icon": "mdi:currency-eur"},
    "vermogen_massarijklaar": {"native_unit_of_measurement": "kW/kg ?", "state_class": SensorStateClass.MEASUREMENT, "icon": "mdi:flash"}, # Check unit
    # Add more specific mappings as needed
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the RDW sensor platform."""
    coordinator: RdwDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    license_plate = coordinator.license_plate

    # Get the list of enabled sensors from options (or default to all if first setup)
    enabled_sensors = entry.options.get(CONF_SENSORS, {key: True for key in RDW_API_KEYS})

    entities = []
    for key in RDW_API_KEYS:
        if enabled_sensors.get(key, False): # Check if sensor is enabled in options
            _LOGGER.debug("Adding RDW sensor for key: %s", key)
            entities.append(RdwSensor(coordinator, key))
        else:
             _LOGGER.debug("Skipping RDW sensor for key: %s (disabled in options)", key)


    # Add Diagnostic Sensors
    entities.extend([
        RdwDiagnosticSensor(coordinator, "last_update_status", "Last Update Status"),
        RdwDiagnosticSensor(coordinator, "last_update_time", "Last Update Time", SensorDeviceClass.TIMESTAMP),
        RdwDiagnosticSensor(coordinator, "consecutive_errors", "Consecutive Update Errors"),
    ])

    async_add_entities(entities, True) # True = update coordinator data before adding


class RdwSensor(RdwEntity, SensorEntity):
    """Representation of an RDW Sensor."""

    def __init__(self, coordinator: RdwDataUpdateCoordinator, data_key: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, data_key)

        # Set entity name based on the data key (will be combined with device name)
        # Example: Device "RDW Vehicle G727FN", Entity "Merk" -> Friendly Name "RDW Vehicle G727FN Merk"
        self._attr_name = data_key.replace("_", " ").replace(" dt", " Date").capitalize()

        # Apply specific properties based on the data key
        description = SENSOR_DESCRIPTIONS.get(data_key, {})
        self._attr_device_class = description.get("device_class")
        self._attr_native_unit_of_measurement = description.get("native_unit_of_measurement")
        self._attr_state_class = description.get("state_class")
        if "icon" in description:
             self._attr_icon = description["icon"]


    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        value = self.coordinator.data.get(self.data_key)

        if value is None:
            return None

        # Handle specific data types, especially dates
        if self._attr_device_class == SensorDeviceClass.DATE and isinstance(value, str):
            # RDW provides dates like 'YYYYMMDD' or 'YYYY-MM-DDTHH:mm:ss.sss'
            parsed_value = parse_datetime(value) # Try parsing ISO format first
            if parsed_value:
                return parsed_value.date()
            # Try parsing YYYYMMDD if ISO fails
            elif len(value) == 8 and value.isdigit():
                 try:
                    return f"{value[0:4]}-{value[4:6]}-{value[6:8]}" # Return as YYYY-MM-DD string for date type
                 except ValueError:
                    return value # Return original if format is unexpected
            else:
                return value # Return original string if parsing fails

        # Convert numeric strings to numbers if appropriate state class is set
        if self._attr_state_class == SensorStateClass.MEASUREMENT and isinstance(value, str):
            try:
                return float(value)
            except (ValueError, TypeError):
                pass # Keep as string if conversion fails

        # Simple yes/no strings -> boolean (optional, depends on preference)
        # if isinstance(value, str):
        #     if value.lower() == 'ja': return True
        #     if value.lower() == 'nee': return False

        return value


class RdwDiagnosticSensor(RdwEntity, SensorEntity):
    """Representation of an RDW Diagnostic Sensor."""
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: RdwDataUpdateCoordinator,
        data_key: str,
        name: str,
        device_class: SensorDeviceClass | None = None
    ) -> None:
        """Initialize the diagnostic sensor."""
        super().__init__(coordinator, data_key)
        self._attr_name = name # Override name generation
        self._attr_device_class = device_class


    @property
    def native_value(self) -> StateType:
        """Return the state of the diagnostic sensor."""
        if self.data_key == "last_update_status":
            return "OK" if not self.coordinator.last_update_error else "Error"
        elif self.data_key == "last_update_time":
            return self.coordinator.last_update_success_timestamp
        elif self.data_key == "consecutive_errors":
            return self.coordinator.error_count
        return None

    @property
    def available(self) -> bool:
        """Diagnostics are always available if the coordinator exists."""
        # Override base availability check as these don't rely on specific data keys
        return self.coordinator is not None

