"""DataUpdateCoordinator for RDW Vehicle Information."""
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import RdwApiClient, RdwApiError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class RdwDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    """Class to manage fetching RDW data."""

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        client: RdwApiClient,
        license_plate: str,
        update_interval: timedelta,
    ):
        """Initialize the coordinator."""
        self.client = client
        self.license_plate = license_plate
        self._error_count = 0
        self._last_update_error = False

        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=update_interval,
        )

    @property
    def error_count(self) -> int:
        """Return the number of consecutive errors."""
        return self._error_count

    @property
    def last_update_error(self) -> bool:
        """Return if the last update resulted in an error."""
        return self._last_update_error

    async def _async_update_data(self) -> dict:
        """Fetch data from API endpoint."""
        _LOGGER.debug("Fetching RDW data for %s", self.license_plate)
        try:
            data = await self.client.get_vehicle_data(self.license_plate)
            self._error_count = 0  # Reset error count on success
            self._last_update_error = False
            return data
        except RdwApiError as err:
            self._error_count += 1
            self._last_update_error = True
            _LOGGER.error("Error communicating with RDW API for %s: %s", self.license_plate, err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
