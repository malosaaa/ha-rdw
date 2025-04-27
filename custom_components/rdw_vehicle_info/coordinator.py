"""DataUpdateCoordinator for RDW Vehicle Information."""
import logging
from datetime import timedelta, datetime

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

# Import the new StolenRegisterError
from .api import RdwApiClient, RdwApiError, RdwApiNoDataError, StolenRegisterError
# Import the new data key constant
from .const import DOMAIN, DATA_KEY_IS_STOLEN

_LOGGER = logging.getLogger(__name__)

# Update the type hint to allow None and include the new key
class RdwDataUpdateCoordinator(DataUpdateCoordinator[dict | None]):
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
        self.last_data: dict | None = None
        # Keep the manual timestamp from the previous fix if you found it necessary
        self.last_update_success_timestamp: datetime | None = None


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

    async def _async_update_data(self) -> dict | None:
        """Fetch data from RDW API and check stolen status."""
        _LOGGER.debug("Fetching all data for RDW vehicle %s", self.license_plate)
        rdw_data = None
        is_stolen = None # Initialize stolen status

        # --- 1. Fetch RDW Data ---
        try:
            rdw_data = await self.client.get_vehicle_data(self.license_plate)
            _LOGGER.debug("Successfully fetched RDW data for %s", self.license_plate)
            # Note: Error counters and timestamp handling moved below after combining data
        except RdwApiNoDataError:
             _LOGGER.warning("No RDW data found for license plate %s, skipping other checks.", self.license_plate)
             # If no RDW data, the whole entry might be invalid, but let's still try stolen check?
             # For now, treat no RDW data as a potential issue but continue if possible
             pass # Continue to stolen check even if RDW fails
        except RdwApiError as err:
            _LOGGER.error("Error fetching RDW data for %s: %s", self.license_plate, err)
            # Continue to stolen check even if RDW fails
            pass

        # --- 2. Check Stolen Status ---
        # Only check stolen status if we at least attempted to get RDW data (or always?)
        # Let's check always, as a plate might be stolen but not have RDW data anymore (e.g., exported)
        try:
             is_stolen = await self.client.async_check_stolen(self.license_plate)
             _LOGGER.debug("Successfully checked stolen status for %s: %s", self.license_plate, is_stolen)
             # is_stolen will be True, False, or None
        except StolenRegisterError as err:
             _LOGGER.error("Error checking stolen register for %s: %s", self.license_plate, err)
             is_stolen = None # Explicitly set to None on error

        # --- 3. Combine and Process Data ---
        combined_data: dict = {}

        # If RDW data was successfully fetched, include it
        if rdw_data:
            combined_data.update(rdw_data)

        # Add the stolen status result
        # is_stolen can be True, False, or None (if check failed)
        combined_data[DATA_KEY_IS_STOLEN] = is_stolen

        # Check if *any* data was obtained (either RDW or stolen status, or both failed)
        # Decide if you want to consider the update successful if *only* the stolen check succeeded
        # or *only* the RDW check succeeded, or only if BOTH succeeded.
        # A common approach is to consider success if at least *some* new data was obtained
        # or if the last_data was updated.

        # Check if the combined data is different from the last stored data
        if self.last_data is not None and combined_data == self.last_data:
            _LOGGER.debug("Combined data has not changed for %s", self.license_plate)
            self._error_count = 0 # Still a successful check cycle
            self._last_update_error = False
            # Update timestamp if you want it to reflect the time of the check, regardless of data change
            self.last_update_success_timestamp = dt_util.now()
            return self.last_data # Return the old data to signal no change

        # If combined data has changed, store the new data
        self.last_data = combined_data

        # Determine if the overall update cycle was successful for timestamp/error tracking
        # Let's consider it successful if we got at least RDW data OR a stolen check result (True/False)
        # If is_stolen is None, the stolen check failed.
        update_successful = bool(rdw_data) or (is_stolen is not None)


        if update_successful:
            self._error_count = 0 # Reset error count on success
            self._last_update_error = False
            self.last_update_success_timestamp = dt_util.now() # Update timestamp on success
            _LOGGER.debug("Combined data updated successfully for %s", self.license_plate)
            return combined_data
        else:
             # If both RDW fetch failed AND stolen check failed or returned None
            self._error_count += 1
            self._last_update_error = True
            _LOGGER.warning("Overall update failed for %s (RDW data: %s, Stolen status: %s)",
                            self.license_plate, "fetched" if rdw_data else "failed", "checked" if is_stolen is not None else "failed")

            # Return last known data on overall failure (consistent with P2000 logic)
            if self.last_data is not None:
                 _LOGGER.debug("Returning last known combined data due to overall error for %s", self.license_plate)
                 return self.last_data
            else:
                 _LOGGER.debug("No last known combined data available, returning None due to overall error for %s", self.license_plate)
                 return None # Return None if no data was ever successfully fetched