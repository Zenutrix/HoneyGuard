from hx711 import HX711
import RPi.GPIO as GPIO
import time
import json

def calibrate(config):
    dout_pin = config['hx711']['dout_pin']
    pd_sck_pin = config['hx711']['pdsck_pin']

    hx711 = HX711(
        dout_pin=dout_pin,
        pd_sck_pin=pd_sck_pin,
        gain=64
    )

    hx711.reset()
    print("Platzieren Sie ein bekanntes Gewicht auf der Waage...")
    time.sleep(5)
    measures = hx711.get_raw_data(num_measures=5)
    average = sum(measures) / len(measures)
    known_weight = float(input("Bitte geben Sie das genaue Gewicht des Objekts ein: "))
    scale_ratio = average / known_weight
    config['hx711']['scale_ratio'] = scale_ratio
    with open('config.json', 'w') as f:
        json.dump(config, f)
    print("Die Kalibrierung wurde abgeschlossen. Der Skalenverhältniswert wurde in der Konfigurationsdatei aktualisiert.")
    GPIO.cleanup()

if __name__ == "__main__":
    with open('config.json', 'r') as f:
        config = json.load(f)
    calibrate(config)
