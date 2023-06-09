import json
import time
import logging
from hx711py.hx711 import HX711

# Logger initialisieren
logging.basicConfig(filename='sensor.log', level=logging.DEBUG)
logger = logging.getLogger()

def load_configuration(file_path):
    try:
        with open(file_path) as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        logger.error(f"Konfigurationsdatei '{file_path}' nicht gefunden.")
    except json.JSONDecodeError:
        logger.error(f"Ungültiges JSON-Format in der Konfigurationsdatei '{file_path}'.")
    return None

def save_configuration(file_path, config):
    try:
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Konfigurationsdatei: {str(e)}")

def initialize_hx711(config):
    hx711_dout_pin = config['hx711']['dout_pin']
    hx711_pdsck_pin = config['hx711']['pdsck_pin']
    hx711 = HX711(
        dout_pin=hx711_dout_pin,
        pd_sck_pin=hx711_pdsck_pin
    )
    hx711.set_reading_format("LSB", "MSB")  # Set the reading format
    hx711.reset()  # Reset the HX711 sensor
    return hx711

def calibrate(hx711):
    input("Please ensure the scale is empty, then press Enter...")
    hx711.tare()  # Reset the scale to 0

    weight = input("Place a known weight on the scale then enter its value in grams... ")
    measures = [hx711.get_raw_data() for _ in range(5)]
    raw_avg = sum(measures) / len(measures) if measures else None

    calibration_factor = float(weight) / raw_avg
    print(f"Calibration factor calculated: {calibration_factor}")
    return calibration_factor

if __name__ == '__main__':
    config_file = 'config.json'
    config = load_configuration(config_file)

    if config is None:
        logger.error("Unable to load the configuration file.")
        exit()

    hx711 = initialize_hx711(config)
    calibration_factor = calibrate(hx711)

    config['hx711']['calibration_factor'] = calibration_factor
    save_configuration(config_file, config)

    print("Calibration factor saved to 'config.json'.")
