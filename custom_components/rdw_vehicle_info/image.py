"""Image platform for RDW Vehicle Information."""
import logging
from typing import cast
import os

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    CONF_ENABLE_IMAGE,
    CONF_SENSORS, # Needed to check if 'merk' is enabled
    IMAGE_PATH_WWW,
    DEFAULT_IMAGE_FILENAME,
)
from .coordinator import RdwDataUpdateCoordinator
from .entity import RdwEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the RDW image platform."""
    # Check if image entity is enabled in options
    if not entry.options.get(CONF_ENABLE_IMAGE, False):
        _LOGGER.debug("RDW Image entity disabled via options for %s", entry.entry_id)
        return

    # Check if the 'merk' sensor is enabled, as we need it for the image
    enabled_sensors = entry.options.get(CONF_SENSORS, {})
    if not enabled_sensors.get("merk", False):
         _LOGGER.warning(
             "Cannot add RDW Image entity for %s because the 'merk' sensor is disabled in options. Enable 'merk' to show the image.",
             entry.entry_id
        )
         return


    coordinator: RdwDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Check if www path exists (where logos should be)
    # Note: This checks the packaged www path, not /local/
    logo_dir = hass.config.path(f"custom_components/{DOMAIN}/www/brand_logos")
    if not await hass.async_add_executor_job(os.path.isdir, logo_dir):
         _LOGGER.warning("RDW brand_logos directory not found at %s. Cannot provide images.", logo_dir)
         # Don't add the entity if the logo directory is missing
         # Alternatively, could add it but have it show unavailable/error state.
         return


    async_add_entities([RdwVehicleImage(coordinator)])


class RdwVehicleImage(RdwEntity, ImageEntity):
    """Representation of an RDW Vehicle Image Entity."""

    _attr_content_type = "image/png" # Assuming PNG logos

    def __init__(self, coordinator: RdwDataUpdateCoordinator) -> None:
        """Initialize the image entity."""
        # Use a fixed key for the image entity type
        super().__init__(coordinator, data_key="vehicle_image")
        ImageEntity.__init__(self, coordinator.hass) # Pass hass to ImageEntity

        self._attr_name = "Vehicle Image" # Override name generation
        self._logo_base_path = f"custom_components/{DOMAIN}/www/brand_logos"
        self._image_url_base = IMAGE_PATH_WWW # Use the registered static path URL base
        self._current_image_url = None
        self._image_last_updated = None # Store timestamp of last successful image load

        # Set initial image URL based on coordinator data if available
        self._update_image_url()


    def _get_logo_filename(self) -> str:
        """Determine the logo filename based on the vehicle brand."""
        if not self.coordinator.data or "merk" not in self.coordinator.data:
            return DEFAULT_IMAGE_FILENAME

        brand = str(self.coordinator.data["merk"]).lower().strip()
        potential_filename = f"{brand}.png"

        # Check if the specific brand logo exists in the www directory
        logo_path = self.hass.config.path(self._logo_base_path, potential_filename)

        if os.path.exists(logo_path): # Use os.path.exists directly
            return potential_filename
        else:
            _LOGGER.debug("Logo for brand '%s' not found at %s, using default.", brand, logo_path)
            return DEFAULT_IMAGE_FILENAME

    def _update_image_url(self) -> None:
         """Update the internal image URL attribute."""
         filename = self._get_logo_filename()
         self._current_image_url = f"{self._image_url_base}/{filename}"
         _LOGGER.debug("Setting image URL for %s to %s", self.unique_id, self._current_image_url)


    @property
    def image_url(self) -> str | None:
        """Return the URL of the image."""
        # Update the URL whenever this property is accessed,
        # ensuring it reflects the latest coordinator data.
        # This is simpler than using async_coordinator_update listener for this case.
        self._update_image_url()
        return self._current_image_url

    async def async_image(self) -> bytes | None:
        """Return bytes of image."""
        # This method fetches the image data directly.
        # Useful if image_url isn't directly usable or needs authentication (not needed here).
        filename = self._get_logo_filename()
        logo_path = self.hass.config.path(self._logo_base_path, filename)

        _LOGGER.debug("Loading image bytes from path: %s", logo_path)

        try:
            # Run blocking I/O in executor
            image_bytes = await self.hass.async_add_executor_job(self._load_image_bytes, logo_path)
            self._image_last_updated = self.hass.datetime.utcnow()
            return image_bytes
        except FileNotFoundError:
            _LOGGER.error("Image file not found at: %s", logo_path)
            # Check if default exists, otherwise return None
            default_path = self.hass.config.path(self._logo_base_path, DEFAULT_IMAGE_FILENAME)
            if os.path.exists(default_path):
                 try:
                    return await self.hass.async_add_executor_job(self._load_image_bytes, default_path)
                 except Exception as e:
                    _LOGGER.error("Error loading default image %s: %s", default_path, e)
                    return None
            return None # Return None if file not found
        except Exception as e:
            _LOGGER.error("Error loading image from %s: %s", logo_path, e)
            raise HomeAssistantError(f"Error loading image: {e}") from e

    def _load_image_bytes(self, path: str) -> bytes:
        """Load image bytes from path (blocking function)."""
        with open(path, "rb") as f:
            return f.read()

    @property
    def image_last_updated(self):
        """Return the timestamp when the image was last loaded."""
        # Return the timestamp of the last successful fetch via async_image
        return self._image_last_updated

    # Ensure image entity updates when coordinator data changes
    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self._update_image_url() # Set initial URL

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_image_url() # Update image URL based on new data
        self.async_write_ha_state()


    @property
    def available(self) -> bool:
        """Return True if coordinator is available and 'merk' data exists (needed for image selection)."""
        # Also check if CONF_ENABLE_IMAGE is true in options.
        options_enabled = self.coordinator.config_entry.options.get(CONF_ENABLE_IMAGE, False)
        merk_available = super().available and self.coordinator.data is not None and "merk" in self.coordinator.data
        return options_enabled and merk_available

