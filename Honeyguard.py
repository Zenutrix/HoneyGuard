import time
import logging
import RPi.GPIO as GPIO
import glob
import json
import bme680
from influxdb import InfluxDBClient
from hx711 import HX711
import subprocess

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

def initialize_influxdb_client(config):
    try:
        influx_host = config['influx']['host']
        influx_port = config['influx']['port']
        influx_db = config['influx']['db']
        client = InfluxDBClient(host=influx_host, port=influx_port)
        if influx_db not in client.get_list_database():
            client.create_database(influx_db)
        client.switch_database(influx_db)
        return client
    except KeyError as e:
        logger.error(f"Fehlende Konfiguration für InfluxDB: {str(e)}")
    except Exception as e:
        logger.error(f"Fehler beim Initialisieren des InfluxDB-Clients: {str(e)}")
    return None

def initialize_hx711(config):
    hx711_enabled = config['hx711']['enabled']
    if hx711_enabled:
        try:
            hx711_dout_pin = config['hx711']['dout_pin']
            hx711_pdsck_pin = config['hx711']['pdsck_pin']
            calibration_factor = config['hx711']['calibration_factor']
            tare = config['hx711']['tare']
            hx711 = HX711(hx711_dout_pin, hx711_pdsck_pin)
            hx711.set_reading_format("MSB", "MSB")
            hx711.set_reference_unit(calibration_factor)
            hx711.reset()
            hx711.tare()
            return hx711
        except KeyError as e:
            logger.error(f"Fehlende Konfiguration für HX711: {str(e)}")
        except Exception as e:
            logger.error(f"Fehler beim Initialisieren des HX711-Sensors: {str(e)}")
    return None


def initialize_bme680(config):
    bme680_enabled = config.get('bme680', {}).get('enabled', False)
    if bme680_enabled:
        try:
            sensor = bme680.BME680()
            sensor.set_humidity_oversample(bme680.OS_2X)
            sensor.set_pressure_oversample(bme680.OS_4X)
            sensor.set_temperature_oversample(bme680.OS_8X)
            sensor.set_filter(bme680.FILTER_SIZE_3)
            sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
            sensor.set_gas_heater_temperature(320)
            sensor.set_gas_heater_duration(150)
            return sensor
        except Exception as e:
            logger.error(f"Fehler beim Initialisieren des BME680-Sensors: {str(e)}")
    return None

def initialize_ds18b20(config):
    ds18b20_enabled = config.get('ds18b20', {}).get('enabled', False)
    if ds18b20_enabled:
        ds18b20_folder = config.get('ds18b20', {}).get('folder', '')
        if ds18b20_folder:
            return ds18b20_folder
        else:
            logger.error("Fehlende Konfiguration für DS18B20: 'folder' nicht gefunden.")
    return None

def initialize_gpio(button_pin, led_pin):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(led_pin, GPIO.OUT)
    return GPIO

def read_weight(hx711):
    if hx711:
        weight = hx711.get_weight(5)
        hx711.power_down()
        hx711.power_up()
        weight_json = {
            "measurement": "weight",
            "time": int(time.time() * 10**9),
            "fields": {
                "value": weight
            }
        }
        client.write_points([weight_json])
        logger.debug("Gewicht erfolgreich in InfluxDB gespeichert.")

def read_temperatures(ds18b20_folder):
    if ds18b20_folder:
        ds18b20_files = glob.glob(ds18b20_folder + '/28-*')
        for i, file in enumerate(ds18b20_files):
            with open(file + '/w1_slave', 'r') as f:
                lines = f.readlines()
                crc_check = lines[0].strip()[-3:]
                if crc_check == 'YES':
                    temperature_line = lines[1]
                    temperature_start = temperature_line.find('t=') + 2
                    temperature_string = temperature_line[temperature_start:].strip()
                    temperature = float(temperature_string) / 1000.0
                    temp_json = {
                        "measurement": f"temperature_sensor{i+1}",
                        "time": int(time.time() * 10**9),
                        "fields": {
                            "value": temperature
                        }
                    }
                    client.write_points([temp_json])
                    logger.debug("Temperatursensor %s erfolgreich in InfluxDB gespeichert.", i+1)

def read_bme680(sensor):
    if sensor and sensor.get_sensor_data():
        bme680_temperature = sensor.data.temperature
        bme680_pressure = sensor.data.pressure
        bme680_humidity = sensor.data.humidity
        bme680_gas_resistance = sensor.data.gas_resistance

        bme680_temp_json = {
            "measurement": "bme680_temperature",
            "time": int(time.time() * 10**9),
            "fields": {
                "value": bme680_temperature
            }
        }
        client.write_points([bme680_temp_json])
        logger.debug("BME680-Temperatur erfolgreich in InfluxDB gespeichert.")

        bme680_pressure_json = {
            "measurement": "bme680_pressure",
            "time": int(time.time() * 10**9),
            "fields": {
                "value": bme680_pressure
            }
        }
        client.write_points([bme680_pressure_json])
        logger.debug("BME680-Druck erfolgreich in InfluxDB gespeichert.")

        bme680_humidity_json = {
            "measurement": "bme680_humidity",
            "time": int(time.time() * 10**9),
            "fields": {
                "value": bme680_humidity
            }
        }
        client.write_points([bme680_humidity_json])
        logger.debug("BME680-Feuchtigkeit erfolgreich in InfluxDB gespeichert.")

        bme680_gas_resistance_json = {
            "measurement": "bme680_gas_resistance",
            "time": int(time.time() * 10**9),
            "fields": {
                "value": bme680_gas_resistance
            }
        }
        client.write_points([bme680_gas_resistance_json])
        logger.debug("BME680-Gaswiderstand erfolgreich in InfluxDB gespeichert.")

def toggle_pause_state():
    global paused
    paused = not paused
    logger.info("Taster gedrückt: Pause-Status geändert zu %s.", paused)

def button_press_handler(channel):
    global button_pressed_start_time, button_press_count
    button_press_count += 1
    if button_press_count == 1:
        button_pressed_start_time = time.time()
    else:
        if (time.time() - button_pressed_start_time) < 2:
            # Taster zweimal schnell hintereinander gedrückt: Programm beenden
            logger.info("Taster zweimal schnell hintereinander gedrückt: Programm wird beendet.")
            GPIO.remove_event_detect(button_pin)
            GPIO.cleanup()
            exit()
        else:
            # Taster einmal gedrückt: Pause einlegen
            button_press_count = 0
            toggle_pause_state()

            # Taster 5 Mal gedrückt: Honeyguard-Service starten
            if button_press_count == 5:
                logger.info("Taster 5 Mal gedrückt: Starte Honeyguard-Service.")
                subprocess.run(["systemctl", "restart", "honeyguard"])

                # LED 2 Mal blinken lassen
                for _ in range(2):
                    GPIO.output(led_pin, GPIO.HIGH)
                    time.sleep(0.5)
                    GPIO.output(led_pin, GPIO.LOW)
                    time.sleep(0.5)

def main_loop():
    while True:
        if not paused:
            read_weight(hx711)
            read_temperatures(ds18b20_folder)
            read_bme680(sensor)

        time.sleep(config['loop_delay'])

if __name__ == '__main__':
    config = load_configuration('config.json')
    if config is None:
        exit()

    client = initialize_influxdb_client(config)
    if client is None:
        exit()

    hx711 = initialize_hx711(config)
    sensor = initialize_bme680(config)
    ds18b20_folder = initialize_ds18b20(config)

    button_pin = config['button']['pin']
    led_pin = config['led']['pin']
    gpio = initialize_gpio(button_pin, led_pin)

    paused = False
    button_pressed_start_time = 0
    button_press_count = 0

    # Taster-Interrupt-Handler hinzufügen
    gpio.add_event_detect(button_pin, GPIO.FALLING, callback=button_press_handler, bouncetime=200)

    try:
        main_loop()
    except KeyboardInterrupt:
        logger.info("Programm beendet durch Tastaturunterbrechung.")
    finally:
        gpio.remove_event_detect(button_pin)
        gpio.cleanup()
