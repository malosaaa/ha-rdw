"""Config flow for RDW Vehicle Information."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from aiohttp import ClientError

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
# SchemaAttributeChecker might not be needed if only using basic schemas now
# from homeassistant.helpers.schema_attribute_checker import SchemaAttributeChecker

from .api import RdwApiClient, RdwApiConnectionError, RdwApiNoDataError
from .const import (
    DOMAIN,
    CONF_LICENSE_PLATE,
    CONF_SENSORS,
    # CONF_ENABLE_IMAGE, # No longer needed here
    RDW_API_KEYS,
    RDW_API_KEYS as DEFAULT_ENABLED_SENSOR_KEYS
)

_LOGGER = logging.getLogger(__name__)

# Schema for user input step (License Plate)
USER_SCHEMA = vol.Schema({
    vol.Required(CONF_LICENSE_PLATE): str,
})

# Function to generate the options schema dynamically
# --- MODIFIED: Removed CONF_ENABLE_IMAGE ---
def create_options_schema(options: Optional[Dict[str, Any]] = None) -> vol.Schema:
    """Create the schema for the options flow."""
    options = options or {}
    # Sort keys alphabetically for consistent UI
    sorted_keys = sorted(RDW_API_KEYS)

    schema_dict = {
        # --- REMOVED Image Option ---
        # Options for each sensor key
        **{
            vol.Optional(
                key,
                # Default based on previous sensor options or initial default list
                default=options.get(CONF_SENSORS, {}).get(key, key in DEFAULT_ENABLED_SENSOR_KEYS)
            ): bool for key in sorted_keys
        }
    }
    return vol.Schema(schema_dict)


class RdwConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for RDW Vehicle Information."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.license_plate: Optional[str] = None
        # --- MODIFIED: Removed CONF_ENABLE_IMAGE ---
        # Store only sensor options now
        self._config_options: Dict[str, Any] = {CONF_SENSORS: {}}


    async def async_validate_license_plate(self, license_plate: str) -> Dict[str, str]:
        """Validate the license plate by making a test API call."""
        # (This function remains unchanged)
        errors: Dict[str, str] = {}
        try:
            session = async_get_clientsession(self.hass)
            client = RdwApiClient(session)
            formatted_plate = license_plate.upper().replace("-", "")
            _LOGGER.debug("Validating license plate: %s", formatted_plate)
            await client.get_vehicle_data(formatted_plate)
            _LOGGER.debug("License plate %s validation successful", formatted_plate)
        except RdwApiConnectionError:
            _LOGGER.warning("Connection error during validation for %s", license_plate)
            errors["base"] = "cannot_connect"
        except RdwApiNoDataError:
            _LOGGER.warning("No data found during validation for %s (invalid plate?)", license_plate)
            errors[CONF_LICENSE_PLATE] = "invalid_license_plate"
        except Exception as e:
            _LOGGER.exception("Unexpected error during license plate validation for %s: %s", license_plate, e)
            errors["base"] = "unknown"
        return errors


    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> config_entries.FlowResult:
        """Handle the initial step where the user enters the license plate."""
        # (This function remains largely unchanged, still calls async_step_options on success)
        errors: Dict[str, str] = {}

        if user_input is not None:
            license_plate_raw = user_input[CONF_LICENSE_PLATE]
            self.license_plate = license_plate_raw.upper().replace("-", "")

            await self.async_set_unique_id(self.license_plate)
            self._abort_if_unique_id_configured()

            errors = await self.async_validate_license_plate(self.license_plate)

            if not errors:
                _LOGGER.debug("License plate %s is valid, proceeding to options.", self.license_plate)
                return await self.async_step_options()

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
            description_placeholders={"error_details": errors.get("base", "")}
        )


    async def async_step_options(self, user_input: Optional[Dict[str, Any]] = None) -> config_entries.FlowResult:
        """Handle the options step where the user selects sensors."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            # --- MODIFIED: Removed CONF_ENABLE_IMAGE ---
            # Only process sensor selections
            self._config_options[CONF_SENSORS] = {
                 key: user_input.get(key, False) for key in RDW_API_KEYS if key in user_input
            }

            _LOGGER.debug("Creating entry for %s with options: %s", self.license_plate, self._config_options)

            # Create the config entry with license plate in data and selections in options
            return self.async_create_entry(
                title=self.license_plate,
                data={CONF_LICENSE_PLATE: self.license_plate},
                options=self._config_options # Now only contains sensor selections
            )

        # Show the options form, pre-filled with defaults
        options_schema = create_options_schema()
        return self.async_show_form(
            step_id="options",
            data_schema=options_schema,
            errors=errors,
             description_placeholders={"license_plate": self.license_plate}
        )


    # Add Options Flow Handler for re-configuration
    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return RdwOptionsFlowHandler(config_entry)


class RdwOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for RDW Vehicle Information."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        # --- MODIFIED: Removed CONF_ENABLE_IMAGE ---
        # Only load sensor options
        self._current_options = {
            CONF_SENSORS: config_entry.options.get(CONF_SENSORS, {})
        }


    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None) -> config_entries.FlowResult:
        """Manage the options for the custom component."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            # --- MODIFIED: Removed CONF_ENABLE_IMAGE ---
            # Only update sensor options
            updated_options = {
                CONF_SENSORS: {
                    key: user_input.get(key, False) for key in RDW_API_KEYS if key in user_input
                }
            }
            _LOGGER.debug("Updating options for %s to: %s", self.config_entry.entry_id, updated_options)
            # Update the config entry's options
            return self.async_create_entry(title="", data=updated_options)

        # Generate schema based on current sensor options stored in the config entry
        # Pass only sensor options to the schema generator
        options_schema = create_options_schema({CONF_SENSORS: self.config_entry.options.get(CONF_SENSORS, {})})

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            errors=errors,
            description_placeholders={"license_plate": self.config_entry.data.get(CONF_LICENSE_PLATE)}
        )
