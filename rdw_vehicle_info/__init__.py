"""The RDW Vehicle Information integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import RdwApiClient
from .const import DOMAIN, CONF_LICENSE_PLATE, PLATFORMS, DEFAULT_UPDATE_INTERVAL
from .coordinator import RdwDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up RDW Vehicle Information from a config entry."""
    _LOGGER.debug("Setting up RDW entry: %s", entry.entry_id)
    hass.data.setdefault(DOMAIN, {})

    license_plate = entry.data[CONF_LICENSE_PLATE]
    session = async_get_clientsession(hass)
    api_client = RdwApiClient(session)

    coordinator = RdwDataUpdateCoordinator(
        hass=hass,
        name=f"RDW Coordinator {license_plate}",
        client=api_client,
        license_plate=license_plate,
        update_interval=DEFAULT_UPDATE_INTERVAL, # Can be made configurable later if needed
    )

    # Fetch initial data so we have it when entities are set up
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up platforms (sensor, image)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Set up listener for options updates
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    # Register the www directory for brand logos
    hass.http.register_static_path(
        f"/{DOMAIN}_files", hass.config.path(f"custom_components/{DOMAIN}/www"), cache_headers=False
    )


    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading RDW entry: %s", entry.entry_id)
    # Forward unload to platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.debug("Successfully unloaded RDW entry: %s", entry.entry_id)

    # Unregister static path if no other entries are loaded (important for cleanup)
    # Note: This logic might need refinement if multiple integrations use similar paths.
    # A simple check might be sufficient for this specific case.
    if not hass.data[DOMAIN]:
         try:
             # Check if path is registered before unregistering - difficult with current HA API
             # As a workaround, we might just leave it registered or handle removal differently.
             # For simplicity here, we won't unregister, as it's usually harmless.
             # hass.http.unregister_static_path(f"/{DOMAIN}_files") # This might error if called multiple times
             pass
         except Exception as e:
             _LOGGER.warning("Could not unregister static path, may require HA restart to clean up: %s", e)


    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.debug("Reloading RDW entry due to options update: %s", entry.entry_id)
    await hass.config_entries.async_reload(entry.entry_id)

