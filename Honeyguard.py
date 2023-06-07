import time
import logging
import RPi.GPIO as GPIO
import glob
import json
import bme680
from influxdb import InfluxDBClient
from hx711 import HX711
from datetime import datetime

# Lade die Konfiguration aus der JSON-Datei
with open('config.json') as f:
    config = json.load(f)

# Logger initialisieren
logging.basicConfig(filename='sensor.log', level=logging.DEBUG)
logger = logging.getLogger()

# InfluxDB-Konfiguration
influx_host = config['influx']['host']
influx_port = config['influx']['port']
influx_db = config['influx']['db']

# HX711-Konfiguration
hx711_enabled = config['hx711']['enabled']
hx711_dout_pin = config['hx711']['dout_pin']
hx711_pdsck_pin = config['hx711']['pdsck_pin']
scale_ratio = config['hx711']['scale_ratio']
tare = config['hx711']['tare']

# DS18B20-Konfiguration
ds18b20_enabled = config['ds18b20']['enabled']
ds18b20_folder = config['ds18b20']['folder']

# BME680-Konfiguration
bme680_enabled = config.get('bme680', {}).get('enabled', False)

# Taster-Konfiguration
button_pin = config['button']['pin']

# LED-Konfiguration
led_pin = config['led']['pin']

# BME680 Sensor initialisieren
sensor = None
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
    except Exception as e:
        logger.error("Fehler beim Initialisieren des BME680-Sensors: %s", str(e))

# InfluxDB-Client initialisieren
client = InfluxDBClient(host=influx_host, port=influx_port)

# Datenbank erstellen, falls sie nicht existiert
if influx_db not in client.get_list_database():
    client.create_database(influx_db)
client.switch_database(influx_db)

# HX711-Objekt initialisieren
hx711 = None
if hx711_enabled:
    hx711 = HX711(dout_pin=hx711_dout_pin, pd_sck_pin=hx711_pdsck_pin)
    hx711.set_scale_ratio(scale_ratio)
    hx711.set_tare(tare)

# Taster-Konfiguration
GPIO.setmode(GPIO.BCM)
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# LED-Konfiguration
GPIO.setup(led_pin, GPIO.OUT)
led_status = False  # Status der LED

paused = False  # Status der Pause
button_pressed_start_time = 0  # Zeitpunkt des Tastendrucks
button_press_count = 0  # Anzahl der Knopfdrücke

while True:
    if not paused:
        # Gewicht auslesen, wenn der HX711-Sensor aktiviert ist
        weight = hx711.get_weight_mean(5) if hx711 and hx711.is_ready() else None

        temperatures = []
        # DS18B20-Temperaturen auslesen, nur wenn Sensoren aktiviert sind
        if ds18b20_enabled:
            ds18b20_files = glob.glob(ds18b20_folder + '/28-*')
            for file in ds18b20_files:
                with open(file + '/w1_slave', 'r') as f:
                    lines = f.readlines()
                    crc_check = lines[0].strip()[-3:]
                    if crc_check == 'YES':
                        temperature_line = lines[1]
                        temperature_start = temperature_line.find('t=') + 2
                        temperature_string = temperature_line[temperature_start:].strip()
                        temperature = float(temperature_string) / 1000.0
                        temperatures.append(temperature)

        # BME680 Sensorwerte auslesen, nur wenn der Sensor aktiviert ist
        bme680_temperature = None
        bme680_pressure = None
        bme680_humidity = None
        bme680_gas_resistance = None
        if sensor:
            if sensor.get_sensor_data():
                bme680_temperature = sensor.data.temperature
                bme680_pressure = sensor.data.pressure
                bme680_humidity = sensor.data.humidity
                bme680_gas_resistance = sensor.data.gas_resistance

        # Aktuelle Zeitstempel erzeugen
        timestamp = datetime.now().isoformat()

        # Messdaten in InfluxDB speichern, nur wenn mindestens ein Sensor aktiviert ist
        if weight is not None:
            weight_json = {
                "measurement": "weight",
                "time": timestamp,
                "fields": {
                    "value": weight
                }
            }
            client.write_points([weight_json])
            logger.debug("Weight successfully written to InfluxDB.")

        for i, temperature in enumerate(temperatures):
            temp_json = {
                "measurement": "temperature_sensor{}".format(i+1),
                "time": timestamp,
                "fields": {
                    "value": temperature
                }
            }
            client.write_points([temp_json])
            logger.debug("Temperature Sensor %s successfully written to InfluxDB.", i+1)

        if bme680_temperature is not None:
            bme680_temp_json = {
                "measurement": "bme680_temperature",
                "time": timestamp,
                "fields": {
                    "value": bme680_temperature
                }
            }
            client.write_points([bme680_temp_json])
            logger.debug("BME680 temperature successfully written to InfluxDB.")

            bme680_pressure_json = {
                "measurement": "bme680_pressure",
                "time": timestamp,
                "fields": {
                    "value": bme680_pressure
                }
            }
            client.write_points([bme680_pressure_json])
            logger.debug("BME680 pressure successfully written to InfluxDB.")

            bme680_humidity_json = {
                "measurement": "bme680_humidity",
                "time": timestamp,
                "fields": {
                    "value": bme680_humidity
                }
            }
            client.write_points([bme680_humidity_json])
            logger.debug("BME680 humidity successfully written to InfluxDB.")

            bme680_gas_resistance_json = {
                "measurement": "bme680_gas_resistance",
                "time": timestamp,
                "fields": {
                    "value": bme680_gas_resistance
                }
            }
            client.write_points([bme680_gas_resistance_json])
            logger.debug("BME680 gas resistance successfully written to InfluxDB.")

        # LED steuern basierend auf dem Wartungsmodus
        if led_status:
            GPIO.output(led_pin, GPIO.LOW)
        else:
            GPIO.output(led_pin, GPIO.HIGH)

    # Tasterstatus überprüfen
    if GPIO.input(button_pin) == GPIO.LOW:
        if button_pressed_start_time == 0:
            button_pressed_start_time = time.time()
        elif time.time() - button_pressed_start_time >= 3:
            if button_press_count == 0:
                button_press_count += 1
            elif button_press_count == 1:
                button_press_count = 0  # Zurücksetzen der Zählung
                paused = not paused  # Pause umschalten
                if paused:
                    led_status = True  # LED einschalten
                else:
                    led_status = False  # LED ausschalten
            button_pressed_start_time = 0
            logger.debug("Button press count: %s", button_press_count)
            logger.debug("Paused status: %s", paused)
    else:
        button_pressed_start_time = 0

    # Eine Pause einfügen, um die Abfrageintervalle anzupassen
    time.sleep(config['pausenzeit'])
