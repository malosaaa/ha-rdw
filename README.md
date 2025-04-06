# RDW Vehicle Information - Home Assistant Custom Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
This custom integration for Home Assistant allows you to fetch vehicle information directly from the Dutch Road Traffic Service (RDW) open data API based on the vehicle's license plate.

It retrieves data from the ["Open Data Gescoorde Voertuigen"](https://opendata.rdw.nl/Voertuigen/Open-Data-Gescoorde-Voertuigen/m9d7-ebf2/about_data) dataset.

## Features

* Fetches a wide range of vehicle data from the RDW.
* Configure multiple vehicles by adding the integration multiple times.
* Select exactly which data points you want as sensor entities via the Options flow.
* Entities are named using the license plate (e.g., `sensor.ab123cd_merk`).
* Provides diagnostic sensors for monitoring the integration's status.
* Uses Home Assistant's UI for configuration (Config Flow).

## Prerequisites

* Home Assistant instance (obvious, right?).
* [HACS (Home Assistant Community Store)](https://hacs.xyz/) installed. This is needed to easily manage the custom component.

## Installation (Using HACS)

This integration is best installed via HACS. If you installed HACS, you can add this repository as a **Custom Repository**.

1.  **Navigate to HACS:** Open Home Assistant and go to HACS in the sidebar.
2.  **Go to Integrations:** Click on "Integrations".
3.  **Add Custom Repository:** Click the three vertical dots (⋮) in the top-right corner and select "Custom repositories".
4.  **Enter Repository Details:**
    * In the "Repository" field, paste the URL of this GitHub repository:
        `https://github.com/malosaaa/ha-rdw` 
    * In the "Category" dropdown, select **"Integration"**.
    * Click the "Add" button.
5.  **Install Integration:**
    * Close the "Custom repositories" dialog.
    * The "RDW Vehicle Information" integration should now appear in your HACS Integrations list. Find it or search for it.
    * Click on the integration card.
    * Click the "Download" button (usually in the bottom right).
    * Confirm the download (select the version - usually the latest is recommended).
6.  **Restart Home Assistant:** After HACS finishes downloading, **you MUST restart Home Assistant** for the integration to be loaded. A prompt should appear, or you can do it manually via Developer Tools -> Server Management -> Restart.

## Configuration

Once installed via HACS and after restarting Home Assistant, you can add your vehicles:

1.  **Navigate to Integrations:** Go to **Settings -> Devices & Services -> Integrations**.
2.  **Add Integration:** Click the "+ Add Integration" button (usually in the bottom right).
3.  **Search:** Search for "RDW Vehicle Information" and click on it.
4.  **Enter License Plate:** You will be prompted to enter the Dutch license plate number (e.g., `AB123CD` or `AB-123-CD`). Dashes and case don't matter; it will be standardized. Click Submit.
5.  **Select Sensors (Options):** If the license plate is valid, you will proceed to an options screen. Here you can check/uncheck boxes for every data field available from the RDW dataset. Only checked items will be created as sensor entities for this vehicle. Click Submit.
6.  **Done!** The integration will be set up for that license plate, and sensor entities will be created based on your selection.
7.  **Add More Vehicles:** To add another vehicle, simply repeat steps 2-6.

**Reconfiguring Sensors:**

You can change which sensors are enabled for a vehicle *after* setup:

1.  Go to **Settings -> Devices & Services -> Integrations**.
2.  Find the RDW Vehicle Information integration entry corresponding to the license plate you want to change.
3.  Click the "CONFIGURE" button on that entry.
4.  Adjust the sensor checkboxes as needed and click Submit. Home Assistant will reload the integration with the new settings.

## Available Sensors

This integration can create sensor entities for almost all data points provided by the RDW "Open Data Gescoorde Voertuigen" dataset. You choose which ones to enable during the configuration / options flow.

Some key examples include:

* `sensor.YOUR_PLATE_merk` (Make, e.g., Fiat)
* `sensor.YOUR_PLATE_handelsbenaming` (Model Name, e.g., 500)
* `sensor.YOUR_PLATE_voertuigsoort` (Vehicle Type, e.g., Personenauto)
* `sensor.YOUR_PLATE_eerste_kleur` (Primary Color)
* `sensor.YOUR_PLATE_vervaldatum_apk_dt` (APK Expiry Date - formatted as Date)
* `sensor.YOUR_PLATE_datum_tenaamstelling_dt` (Registration Date - formatted as Date)
* `sensor.YOUR_PLATE_catalogusprijs` (Catalog Price)
* `sensor.YOUR_PLATE_massa_rijklaar` (Mass Ready-to-drive)
* `sensor.YOUR_PLATE_cilinderinhoud` (Cylinder Capacity)
* ... and many more!

It also creates diagnostic sensors like:

* `sensor.YOUR_PLATE_last_update_status`
* `sensor.YOUR_PLATE_last_update_time`
* `sensor.YOUR_PLATE_consecutive_update_errors`

*(Replace `YOUR_PLATE` with the actual license plate, e.g., `ab123cd`)*

## Troubleshooting

* **Integration not found after HACS download:** Ensure you restarted Home Assistant after downloading via HACS.
* **"Config flow could not be loaded":** Double-check the installation steps and restart Home Assistant. Check Home Assistant logs for detailed errors.
* **"Failed to connect" / "Invalid license plate" during setup:** Verify your internet connection and ensure the license plate entered is correct and exists in the RDW database.
* **Sensors show "Unavailable":** Check the diagnostic sensors for the specific license plate. Also check Home Assistant logs (Settings -> System -> Logs) for errors related to `rdw_vehicle_info`.

If you encounter issues, please check the existing issues on GitHub first, and if your problem isn't listed, feel free to open a new issue here:
[https://github.com/malosaaa/ha-rdw/issues](https://github.com/malosaaa/ha-rdw/issues) 

## Contributing

Contributions are welcome! Feel free to open Pull Requests or Issues on the GitHub repository.

## License

This project is licensed under the [Apache License 2.0](LICENSE).  
**(You need to choose a license and add a `LICENSE` file to your repository! Apache 2.0 or MIT are common choices).**

## Disclaimer

* This integration relies on the open data provided by the RDW (Dutch Road Traffic Service). Availability and accuracy depend on their service.
* This integration is not affiliated with or endorsed by the RDW.

---
