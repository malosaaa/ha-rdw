"""Base entity for RDW Vehicle Information."""
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, CONF_LICENSE_PLATE
from .coordinator import RdwDataUpdateCoordinator


class RdwEntity(CoordinatorEntity[RdwDataUpdateCoordinator]):
    """Base class for RDW entities."""

    _attr_has_entity_name = True # Use automatic naming based on device and entity name

    def __init__(self, coordinator: RdwDataUpdateCoordinator, data_key: str) -> None:
        """Initialize the RDW entity."""
        super().__init__(coordinator)
        self.data_key = data_key
        self._license_plate = coordinator.license_plate

        # Unique ID uses license plate and data key
        self._attr_unique_id = f"{self._license_plate}_{self.data_key}".lower()

        # Link all sensors for this license plate to one device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._license_plate)},
            name=f"RDW Vehicle {self._license_plate}",
            manufacturer=MANUFACTURER,
            model=coordinator.data.get("merk", "Unknown") + " " + coordinator.data.get("handelsbenaming", ""),
            entry_type=None, # Use None for service-provided devices
            configuration_url="https://opendata.rdw.nl/",
            sw_version=coordinator.data.get("typegoedkeuringsnummer"), # Example using an available field
            # hw_version can be added if relevant data exists
        )

    @property
    def available(self) -> bool:
        """Return True if coordinator is available and data key exists."""
        return super().available and self.coordinator.data is not None and self.data_key in self.coordinator.data
