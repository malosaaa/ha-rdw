"""API Client for RDW Vehicle Information."""
import asyncio
import logging
import socket
from typing import Any

import async_timeout
from aiohttp import ClientError, ClientSession
from bs4 import BeautifulSoup # Import BeautifulSoup

from .const import (
    API_BASE_URL, API_PARAM_LICENSE_PLATE, API_TIMEOUT,
    STOLEN_REGISTER_URL, STOLEN_REGISTER_PARAM_SEARCH, STOLEN_REGISTER_PARAM_LANG
)

_LOGGER = logging.getLogger(__name__)

# ... (Your existing RdwApiError, RdwApiConnectionError, RdwApiNoDataError classes remain the same) ...
class RdwApiError(Exception):
    """Generic RDW API Error."""

class RdwApiConnectionError(RdwApiError):
    """RDW API Connection Error."""

class RdwApiNoDataError(RdwApiError):
    """RDW API No Data Error (e.g., invalid license plate)."""

# Add a new exception for scraping errors
class StolenRegisterError(RdwApiError):
    """Error fetching data from Stolen Register."""

class RdwApiClient:
    """RDW API Client."""

    def __init__(self, session: ClientSession):
        """Initialize the API client."""
        self._session = session
        self._rdw_base_url = API_BASE_URL
        self._stolen_base_url = STOLEN_REGISTER_URL

    async def get_vehicle_data(self, license_plate: str) -> dict[str, Any]:
        """Fetch vehicle data for a given license plate from RDW."""
        # Ensure license plate is uppercase and formatted correctly (optional, API might handle)
        formatted_plate = license_plate.upper().replace("-", "")
        url = f"{self._rdw_base_url}?{API_PARAM_LICENSE_PLATE}={formatted_plate}"
        _LOGGER.debug("Requesting RDW data from: %s", url)

        try:
            async with async_timeout.timeout(API_TIMEOUT):
                response = await self._session.get(url)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

                data = await response.json()
                _LOGGER.debug("Received RDW data: %s", data)

                if not data or not isinstance(data, list) or len(data) == 0:
                    _LOGGER.warning("No data found for license plate %s from RDW", formatted_plate)
                    raise RdwApiNoDataError(f"No data found from RDW for license plate {formatted_plate}")

                # API returns a list with one item
                return data[0]

        except asyncio.TimeoutError as exc:
            _LOGGER.error("Timeout occurred while requesting RDW data for %s: %s", formatted_plate, exc)
            raise RdwApiConnectionError(f"Timeout connecting to RDW API for {formatted_plate}") from exc
        except (ClientError, socket.gaierror) as exc:
            _LOGGER.error("Communication error occurred while requesting RDW data for %s: %s", formatted_plate, exc)
            raise RdwApiConnectionError(f"Communication error with RDW API for {formatted_plate}") from exc
        except Exception as exc:
            _LOGGER.error("An unexpected error occurred while fetching RDW data for %s: %s", formatted_plate, exc)
            # Catch any other unexpected exceptions during RDW fetch
            raise RdwApiError(f"Unexpected error during RDW fetch for {formatted_plate}: {exc}") from exc


    async def async_check_stolen(self, license_plate: str) -> bool | None:
        """Check if a license plate is listed as stolen."""
        formatted_plate = license_plate.upper().replace("-", "")
        # Construct the URL for the stolen register search
        url = f"{self._stolen_base_url}?{STOLEN_REGISTER_PARAM_LANG}=1&{STOLEN_REGISTER_PARAM_SEARCH}={formatted_plate}"
        _LOGGER.debug("Checking stolen register for: %s (URL: %s)", formatted_plate, url)

        try:
            async with async_timeout.timeout(API_TIMEOUT): # Reuse the same timeout constant
                response = await self._session.get(url)
                response.raise_for_status() # Raise HTTPError for bad responses

                html = await response.text()
                _LOGGER.debug("Received HTML from stolen register (partial): %s...", html[:500]) # Log start of HTML

                soup = BeautifulSoup(html, "html.parser")

                # --- Parsing Logic ---
                # Based on your HTML snippet, the "no result" message is in a specific div within panel-4
                no_result_div = soup.select_one("#panel-4 div.card-block p")

                # Check if the 'no result' message paragraph exists and contains the expected text
                if no_result_div and "Uw zoekopdracht naar het object heeft geen resultaat opgeleverd" in no_result_div.text:
                    _LOGGER.debug("Stolen register check: No stolen object found for %s", formatted_plate)
                    return False # Not registered as stolen
                else:
                     # If the 'no result' div/text is NOT found, assume it IS listed (stolen)
                    _LOGGER.debug("Stolen register check: Object found (likely stolen) for %s", formatted_plate)
                    return True # Listed as stolen

        except asyncio.TimeoutError as exc:
            _LOGGER.error("Timeout occurred while checking stolen register for %s: %s", formatted_plate, exc)
            # Return None to indicate stolen status could not be determined
            return None
        except (ClientError, socket.gaierror) as exc:
            _LOGGER.error("Communication error occurred while checking stolen register for %s: %s", formatted_plate, exc)
             # Return None to indicate stolen status could not be determined
            return None
        except Exception as exc:
            # Catch any other unexpected exceptions during scraping/parsing
            _LOGGER.error("An unexpected error occurred while checking stolen register for %s: %s", formatted_plate, exc)
            # Return None to indicate stolen status could not be determined
            return None