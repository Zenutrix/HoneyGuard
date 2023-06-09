import json
from hx711 import HX711
import time

def calibrate():
    # Load configuration
    with open('config.json', 'r') as f:
        config = json.load(f)

    # Create HX711 object
    hx = HX711(
        dout_pin=config['hx711']['dout_pin'],
        pd_sck_pin=config['hx711']['pdsck_pin']
    )

    # Reset HX711
    hx.reset()

    print("Now, please put the known weight on the scale.")

    # Read raw data from HX711
    raw_data = hx.get_raw_data(times=5)

    # Calculate average raw reading
    average_raw = sum(raw_data) / len(raw_data)

    # Ask for the weight of the known weight
    known_weight = float(input("Please enter the weight of the known weight in grams: "))

    # Calculate scale ratio
    scale_ratio = average_raw / known_weight

    # Update configuration with scale ratio
    config['hx711']['scale_ratio'] = scale_ratio

    print("Now, please remove all weight from the scale.")

    # Read raw data from HX711 for tare
    tare_data = hx.get_raw_data(times=5)

    # Calculate average tare reading
    average_tare = sum(tare_data) / len(tare_data)

    # Update configuration with tare
    config['hx711']['tare'] = -average_tare

    # Save configuration
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)

    print("Calibration completed and values stored in config.json")

if __name__ == "__main__":
    calibrate()
