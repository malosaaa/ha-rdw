"""Constants for the RDW Vehicle Information integration."""
from typing import Final
from datetime import timedelta
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

DOMAIN: Final = "rdw_vehicle_info"
MANUFACTURER: Final = "RDW (Dutch Road Authority)"

# Configuration Keys
CONF_LICENSE_PLATE: Final = "license_plate"
CONF_SENSORS: Final = "sensors"
CONF_ENABLE_IMAGE: Final = "enable_image"

# API Details
API_BASE_URL: Final = "https://opendata.rdw.nl/resource/m9d7-ebf2.json"
API_PARAM_LICENSE_PLATE: Final = "kenteken"
API_TIMEOUT: Final = 10  # seconds

# Update Interval
DEFAULT_UPDATE_INTERVAL: Final = timedelta(hours=24) # RDW data rarely changes rapidly

# Data Keys from RDW API (Used for sensor selection and naming)
# Add ALL keys from the sample data you want to potentially expose
# Keep names lowercase as they appear in the JSON, but map them to friendly names maybe
RDW_API_KEYS: Final[list[str]] = [
    "kenteken", "voertuigsoort", "merk", "handelsbenaming", "vervaldatum_apk",
    "datum_tenaamstelling", "bruto_bpm", "inrichting", "aantal_zitplaatsen",
    "eerste_kleur", "tweede_kleur", "aantal_cilinders", "cilinderinhoud",
    "massa_ledig_voertuig", "toegestane_maximum_massa_voertuig", "massa_rijklaar",
    "maximum_massa_trekken_ongeremd", "maximum_trekken_massa_geremd",
    "datum_eerste_toelating", "datum_eerste_tenaamstelling_in_nederland",
    "wacht_op_keuren", "catalogusprijs", "wam_verzekerd",
    "maximale_constructiesnelheid", "aantal_deuren", "aantal_wielen", "lengte",
    "breedte", "europese_voertuigcategorie", "technische_max_massa_voertuig",
    "type", "typegoedkeuringsnummer", "variant", "uitvoering",
    "volgnummer_wijziging_eu_typegoedkeuring", "vermogen_massarijklaar",
    "wielbasis", "export_indicator", "openstaande_terugroepactie_indicator",
    "taxi_indicator", "maximum_massa_samenstelling",
    "jaar_laatste_registratie_tellerstand", "tellerstandoordeel",
    "code_toelichting_tellerstandoordeel", "tenaamstellen_mogelijk",
    "vervaldatum_apk_dt", "datum_tenaamstelling_dt", "datum_eerste_toelating_dt",
    "datum_eerste_tenaamstelling_in_nederland_dt", "hoogte_voertuig",
    "zuinigheidsclassificatie",
    # Exclude API links unless specifically needed
    # "api_gekentekende_voertuigen_assen", ...
]

# Sensor configuration schema used in config flow options
SENSOR_SCHEMA = vol.Schema({
    vol.Optional(key, default=True): cv.boolean for key in RDW_API_KEYS
})

# Image constants
IMAGE_PATH_LOCAL = f"/local/{DOMAIN}/brand_logos" # Path if users put logos in config/www/rdw_vehicle_info/brand_logos
IMAGE_PATH_WWW = f"/{DOMAIN}_files/brand_logos" # Path if logos are packaged with the integration
DEFAULT_IMAGE_FILENAME = "default.png"

PLATFORMS: Final[list[str]] = ["sensor", "image"]

# Diagnostics
DIAG_CONFIG_ENTRY = "config_entry"
DIAG_COORDINATOR_DATA = "coordinator_data"
DIAG_OPTIONS = "options"
