from influxdb import InfluxDBClient
from hx711 import HX711
import time
import RPi.GPIO as GPIO
import glob
import json
import bme680

# Lade die Konfiguration aus der JSON-Datei
with open('config.json') as f:
    config = json.load(f)

# InfluxDB-Konfiguration
influx_host = config['influx']['host']
influx_port = config['influx']['port']
influx_db = config['influx']['db']
influx_user = config['influx']['user']
influx_password = config['influx']['password']

# HX711-Konfiguration
hx711_dout_pin = config['hx711']['dout_pin']
hx711_pdsck_pin = config['hx711']['pdsck_pin']
scale_ratio = config['hx711']['scale_ratio']

# DS18B20-Konfiguration
ds18b20_folder = config['ds18b20']['folder']

# Taster-Konfiguration
button_pin = config['button']['pin']

# LED-Konfiguration
led_pin = config['led']['pin']

# BME680 Sensor initialisieren
sensor = bme680.BME680()

# InfluxDB-Client initialisieren
client = InfluxDBClient(host=influx_host, port=influx_port, username=influx_user, password=influx_password)
client.switch_database(influx_db)

# HX711-Objekt initialisieren
hx711 = HX711(dout_pin=hx711_dout_pin, pd_sck_pin=hx711_pdsck_pin)

# Gewichtsfaktor (Kalibrierungsfaktor) einstellen
hx711.set_scale_ratio(scale_ratio)

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
        # Gewicht auslesen
        weight = hx711.get_weight_mean(5)

        temperatures = []
        # DS18B20-Temperaturen auslesen
        for file in ds18b20_files:
            with open(file + '/w1_slave', 'r') as f:
                lines = f.readlines()
                temperature_line = lines[1]
                temperature_start = temperature_line.find('t=') + 2
                temperature_string = temperature_line[temperature_start:].strip()
                temperature = float(temperature_string) / 1000.0
                temperatures.append(temperature)

        # BME680 Sensorwerte auslesen
        if sensor.get_sensor_data():
            bme680_temperature = sensor.data.temperature
            bme680_pressure = sensor.data.pressure
            bme680_humidity = sensor.data.humidity
            bme680_air_quality = sensor.data.air_quality_score

        # Aktuelle Zeitstempel erzeugen
        timestamp = int(time.time() * 1000)

        # Messdaten in InfluxDB speichern
        json_body = [
            {
                "measurement": "weight_temperature",
                "time": timestamp,
                "fields": {
                    "weight": weight,
                    "bme680_temperature": bme680_temperature,
                    "bme680_pressure": bme680_pressure,
                    "bme680_humidity": bme680_humidity,
                    "bme680_air_quality": bme680_air_quality,
                }
            }
        ]
        for i, temperature in enumerate(temperatures):
            json_body[0]["fields"]["temperature_sensor{}".format(i+1)] = temperature
        client.write_points(json_body)

        print("Daten erfolgreich in InfluxDB gespeichert.")

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
