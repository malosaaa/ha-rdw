"""The RDW Vehicle Information integration."""
import logging
import os  # <-- Import os for directory checking

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import RdwApiClient # Assuming this is correctly named in your api.py
from .const import DOMAIN, CONF_LICENSE_PLATE, PLATFORMS, DEFAULT_UPDATE_INTERVAL
from .coordinator import RdwDataUpdateCoordinator # Assuming this is correctly named in your coordinator.py

_LOGGER = logging.getLogger(__name__)

# Define a key to track registration status in hass.data
DATA_FILES_REGISTERED = f"{DOMAIN}_files_registered"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up RDW Vehicle Information from a config entry."""
    _LOGGER.debug("Setting up RDW entry: %s (Title: %s)", entry.entry_id, entry.title)
    hass.data.setdefault(DOMAIN, {})

    # --- FIX: Register static path only once ---
    if DATA_FILES_REGISTERED not in hass.data:
        _LOGGER.debug("Attempting to register static path %s_files", DOMAIN)
        hass.data[DATA_FILES_REGISTERED] = True # Mark as attempted prevent re-entry
        try:
            www_path = hass.config.path(f"custom_components/{DOMAIN}/www")
            # Check if the www directory exists before trying to register
            if await hass.async_add_executor_job(os.path.isdir, www_path):
                hass.http.register_static_path(
                    f"/{DOMAIN}_files", www_path, cache_headers=False
                )
                _LOGGER.info("Successfully registered static path for %s www directory.", DOMAIN)
            else:
                _LOGGER.debug("Integration www directory not found at %s, skipping static path registration.", www_path)
        except Exception as e:
            # Log error but continue setup - static path is for optional images
            _LOGGER.error("Error registering static path '/%s_files': %s", DOMAIN, e, exc_info=True)
    # --- END FIX ---

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

    # --- The original register_static_path call is removed from here ---

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading RDW entry: %s", entry.entry_id)
    # Forward unload to platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.debug("Successfully unloaded RDW entry: %s", entry.entry_id)

        # --- Optional: Clean up registration flag if last entry ---
        # Note: Does not actually unregister path as that's unreliable via hass.http
        if not hass.data[DOMAIN] and DATA_FILES_REGISTERED in hass.data:
             _LOGGER.debug("Last RDW entry unloaded, removing registration flag.")
             hass.data.pop(DATA_FILES_REGISTERED, None)

    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.debug("Reloading RDW entry due to options update: %s", entry.entry_id)
    await hass.config_entries.async_reload(entry.entry_id)