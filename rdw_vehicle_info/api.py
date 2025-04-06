"""API Client for RDW Vehicle Information."""
import asyncio
import logging
import socket
from typing import Any

import async_timeout
from aiohttp import ClientError, ClientSession

from .const import API_BASE_URL, API_PARAM_LICENSE_PLATE, API_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class RdwApiError(Exception):
    """Generic RDW API Error."""

class RdwApiConnectionError(RdwApiError):
    """RDW API Connection Error."""

class RdwApiNoDataError(RdwApiError):
    """RDW API No Data Error (e.g., invalid license plate)."""


class RdwApiClient:
    """RDW API Client."""

    def __init__(self, session: ClientSession):
        """Initialize the API client."""
        self._session = session
        self._base_url = API_BASE_URL

    async def get_vehicle_data(self, license_plate: str) -> dict[str, Any]:
        """Fetch vehicle data for a given license plate."""
        # Ensure license plate is uppercase and formatted correctly (optional, API might handle)
        formatted_plate = license_plate.upper().replace("-", "")
        url = f"{self._base_url}?{API_PARAM_LICENSE_PLATE}={formatted_plate}"
        _LOGGER.debug("Requesting RDW data from: %s", url)

        try:
            async with async_timeout.timeout(API_TIMEOUT):
                response = await self._session.get(url)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

                data = await response.json()
                _LOGGER.debug("Received RDW data: %s", data)

                if not data or not isinstance(data, list) or len(data) == 0:
                    _LOGGER.warning("No data found for license plate %s", formatted_plate)
                    raise RdwApiNoDataError(f"No data found for license plate {formatted_plate}")

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
            raise RdwApiError(f"Unexpected error for {formatted_plate}: {exc}") from exc

