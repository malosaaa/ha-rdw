"""Constants for the RDW Vehicle Information integration."""
from typing import Final
from datetime import timedelta
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.const import Platform # Import Platform

DOMAIN: Final = "rdw_vehicle_info"
MANUFACTURER: Final = "RDW (Dutch Road Authority)"

# Configuration Keys
CONF_LICENSE_PLATE: Final = "license_plate"
CONF_SENSORS: Final = "sensors"
CONF_ENABLE_IMAGE: Final = "enable_image" # Keep or remove based on your final image entity plan

# API Details
API_BASE_URL: Final = "https://opendata.rdw.nl/resource/m9d7-ebf2.json"
API_PARAM_LICENSE_PLATE: Final = "kenteken"
API_TIMEOUT: Final = 10 # seconds

# Stolen Objects Register Details
STOLEN_REGISTER_URL: Final = "https://gestolenobjectenregister.nl/registration_overview/"
STOLEN_REGISTER_PARAM_SEARCH: Final = "df_search"
STOLEN_REGISTER_PARAM_LANG: Final = "l" # Language param, '1' for Dutch

# Update Interval
DEFAULT_UPDATE_INTERVAL: Final = timedelta(hours=24) # RDW data rarely changes rapidly

# Data Keys from RDW API (Used for sensor selection and naming)
# ... (your existing RDW_API_KEYS list remains the same) ...
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
]

# New data key for the stolen status
DATA_KEY_IS_STOLEN: Final = "is_stolen"

# Sensor configuration schema used in config flow options
# ... (your existing SENSOR_SCHEMA remains the same, stolen check is a separate entity) ...
SENSOR_SCHEMA = vol.Schema({
    vol.Optional(key, default=True): cv.boolean for key in RDW_API_KEYS
})

# Image constants
# ... (your existing Image constants remain the same) ...
IMAGE_PATH_LOCAL = f"/local/{DOMAIN}/brand_logos"
IMAGE_PATH_WWW = f"/{DOMAIN}_files/brand_logos"
DEFAULT_IMAGE_FILENAME = "default.png"

# Add binary_sensor to platforms
PLATFORMS: Final[list[Platform]] = [Platform.SENSOR, Platform.IMAGE, Platform.BINARY_SENSOR]

# Diagnostics
DIAG_CONFIG_ENTRY: Final = "config_entry"
DIAG_COORDINATOR_DATA: Final = "coordinator_data"
DIAG_OPTIONS: Final = "options"