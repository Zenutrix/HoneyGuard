from influxdb import InfluxDBClient
from hx711 import HX711
import time
import RPi.GPIO as GPIO
import glob
import json
import bme680
import os

# Lade die Konfiguration aus der JSON-Datei
with open('config.json') as f:
    config = json.load(f)

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
    except Exception as e:
        print("Fehler beim Initialisieren des BME680-Sensors:", str(e))

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

# Funktion zum Auslesen der Temperatur
def read_temperature():
    # Pfad zum Sensor
    sensor_folder = glob.glob('/sys/bus/w1/devices/28-*')[0]
    sensor_path = os.path.join(sensor_folder, 'w1_slave')

    # Sensor auslesen
    with open(sensor_path, 'r') as file:
        lines = file.readlines()

    # Überprüfen, ob das Auslesen erfolgreich war
    if lines[0].strip()[-3:] == 'YES':
        # Temperatur extrahieren und konvertieren
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temperature_string = lines[1][equals_pos+2:]
            temperature = float(temperature_string) / 1000.0
            return temperature
    else:
        # Fehler beim Auslesen
        return None

# Hauptprogramm
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
        bme680_air_quality = None
        if sensor:
            if sensor.get_sensor_data() and sensor.data.heat_stable:
                bme680_temperature = sensor.data.temperature
                bme680_pressure = sensor.data.pressure
                bme680_humidity = sensor.data.humidity
                bme680_air_quality = sensor.data.air_quality_score

        # Aktuelle Zeitstempel erzeugen
        timestamp = int(time.time() * 1000)

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

            print("Gewicht erfolgreich in InfluxDB gespeichert.")

        for i, temperature in enumerate(temperatures):
            temp_json = {
                "measurement": "temperature_sensor{}".format(i+1),
                "time": timestamp,
                "fields": {
                    "value": temperature
                }
            }
            client.write_points([temp_json])

            print("Temperatur Sensor {} erfolgreich in InfluxDB gespeichert.".format(i+1))

        if bme680_temperature is not None:
            bme680_json = {
                "measurement": "bme680",
                "time": timestamp,
                "fields": {
                    "temperature": bme680_temperature,
                    "pressure": bme680_pressure,
                    "humidity": bme680_humidity,
                    "air_quality": bme680_air_quality
                }
            }
            client.write_points([bme680_json])

            print("BME680-Daten erfolgreich in InfluxDB gespeichert.")

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
    else:
        button_pressed_start_time = 0

    # Eine Pause einfügen, um die Abfrageintervalle anzupassen
    time.sleep(config['pausenzeit'])
