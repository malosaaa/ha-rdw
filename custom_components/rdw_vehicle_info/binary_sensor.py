"""Binary Sensor platform for RDW Vehicle Information."""
import logging

# Import BinarySensorEntity and BinarySensorDeviceClass
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

# Import constants and the base entity
from .const import DOMAIN, DATA_KEY_IS_STOLEN
from .coordinator import RdwDataUpdateCoordinator # Ensure coordinator is imported
from .entity import RdwEntity # Ensure base entity is imported

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the RDW binary sensor platform."""
    # Get the coordinator instance for this config entry
    coordinator: RdwDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    # Add the stolen status binary sensor
    _LOGGER.debug("Adding RDW Stolen Status binary sensor for %s", coordinator.license_plate)
    entities.append(RdwStolenBinarySensor(coordinator))

    # Add other binary sensors here if needed in the future

    # Add the created entities to Home Assistant
    # The 'True' parameter requests an initial update of the coordinator data
    # before the entities are added to the state machine.
    async_add_entities(entities, True)


class RdwStolenBinarySensor(RdwEntity, BinarySensorEntity):
    """Representation of the RDW Stolen Status binary sensor."""

    # Use the SAFETY device class for stolen status
    _attr_device_class = BinarySensorDeviceClass.SAFETY
    # Optional: set a custom icon for the binary sensor
    # _attr_icon = "mdi:car-theft"


    def __init__(self, coordinator: RdwDataUpdateCoordinator) -> None:
        """Initialize the binary sensor."""
        # Call the base entity constructor. Use a unique key specific to this sensor type.
        # We pass a descriptive string as the data_key for the base class's unique ID generation.
        super().__init__(coordinator, "stolen_status_binary")
        # Set the unique ID for this specific entity instance.
        # This is redundant if base class unique ID is sufficient, but explicit is clear.
        self._attr_unique_id = f"{self.coordinator.license_plate}_is_stolen".lower()
        # Set the name for the entity. With _attr_has_entity_name = True in the base class,
        # this name will be appended to the device name in the UI.
        self._attr_name = "Stolen Status"


    @property
    def is_on(self) -> bool | None:
        """Return true if the car is listed as stolen."""
        # Check if the coordinator has data and the specific key for stolen status exists
        if not self.coordinator.data or DATA_KEY_IS_STOLEN not in self.coordinator.data:
            # Return None if data or the key is missing, indicating an unknown state
            return None

        # Get the stolen status value from the coordinator's data
        # This value is True, False, or None as determined by the API client
        stolen_status = self.coordinator.data.get(DATA_KEY_IS_STOLEN)

        # For a binary sensor, the state is True (on) or False (off).
        # If the stolen_status is True, the binary sensor is 'on'.
        # If the stolen_status is False, the binary sensor is 'off'.
        # If the stolen_status is None (check failed), the state is unknown (handled by returning None above).
        if stolen_status is True:
            return True
        elif stolen_status is False:
            return False

        # This line should ideally not be reached if the initial check for None handles it,
        # but as a safeguard, return None if stolen_status was None.
        return None


    @property
    def available(self) -> bool:
        """Return True if the entity is available."""
         # This binary sensor should be available if the coordinator is available,
         # even if the stolen check specifically failed (the state will be unknown/None).
        return self.coordinator.last_update_success

