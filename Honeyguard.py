from influxdb import InfluxDBClient
from hx711 import HX711
import time
import RPi.GPIO as GPIO
import Adafruit_SSD1306
from PIL import Image, ImageDraw, ImageFont
import glob

# InfluxDB-Konfiguration
influx_host = 'localhost'
influx_port = 8086
influx_db = 'measured_data'
influx_user = 'your_username'
influx_password = 'your_password'

# HX711-Konfiguration
hx711_dout_pin = 5
hx711_pdsck_pin = 6

# DS18B20-Konfiguration
ds18b20_folder = '/sys/bus/w1/devices/'
ds18b20_files = glob.glob(ds18b20_folder + '28*')

# Taster-Konfiguration
button_pin = 12

# LED-Konfiguration
led_pin = 16  # GPIO-Pin für die LED

# OLED-Display-Konfiguration
oled_width = 128
oled_height = 64

# InfluxDB-Client initialisieren
client = InfluxDBClient(host=influx_host, port=influx_port, username=influx_user, password=influx_password)
client.switch_database(influx_db)

# HX711-Objekt initialisieren
hx711 = HX711(dout_pin=hx711_dout_pin, pd_sck_pin=hx711_pdsck_pin)

# Gewichtsfaktor (Kalibrierungsfaktor) einstellen
hx711.set_scale(1)  # Passen Sie den Faktor entsprechend an

# TARA-Gewicht einstellen (Optionaler Schritt)
hx711.tare()

# Taster-Konfiguration
GPIO.setmode(GPIO.BCM)
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# LED-Konfiguration
GPIO.setup(led_pin, GPIO.OUT)
led_status = False  # Status der LED

# OLED-Display initialisieren
oled = Adafruit_SSD1306.SSD1306_128_64(rst=None)
oled.begin()
oled.clear()
oled.display()

# Schriftart für den Text auf dem Display
font = ImageFont.load_default()

# Funktion zum Anzeigen des Gewichts und der Temperatur auf dem Display
def display_data(weight, temperatures):
    image = Image.new('1', (oled_width, oled_height))
    draw = ImageDraw.Draw(image)
    draw.text((0, 0), 'Gewicht:', font=font, fill=255)
    draw.text((0, 20), '{:.2f} g'.format(weight), font=font, fill=255)
    draw.text((0, 40), 'Temperaturen:', font=font, fill=255)
    for i, temperature in enumerate(temperatures):
        draw.text((0, 60 + (i * 10)), 'Sensor {}: {:.2f} °C'.format(i+1, temperature), font=font, fill=255)
    oled.image(image)
    oled.display()

# Standby-Text auf dem Display anzeigen
def display_standby_text():
    image = Image.new('1', (oled_width, oled_height))
    draw = ImageDraw.Draw(image)
    draw.text((0, 0), 'Standby', font=font, fill=255)
    oled.image(image)
    oled.display()

paused = False  # Status der Pause
button_pressed_start_time = 0  # Zeitpunkt des Tastendrucks
button_press_count = 0  # Anzahl der Knopfdrücke

while True:
    if not paused:
        # Gewicht auslesen
        weight = hx711.get_weight_mean(5)  # Durchschnitt über 5 Messungen

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

        # Aktuelle Zeitstempel erzeugen
        timestamp = int(time.time() * 1000)

        # Messdaten in InfluxDB speichern
        json_body = [
            {
                "measurement": "weight_temperature",
                "time": timestamp,
                "fields": {
                    "weight": weight,
                }
            }
        ]
        for i, temperature in enumerate(temperatures):
            json_body[0]["fields"]["temperature_sensor{}".format(i+1)] = temperature
        client.write_points(json_body)

        print("Daten erfolgreich in InfluxDB gespeichert.")

        # Gewicht und Temperaturen auf dem OLED-Display anzeigen
        display_data(weight, temperatures)

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
                    display_standby_text()  # "Standby" anzeigen
                    led_status = True  # LED einschalten
                else:
                    display_data(weight, temperatures)
                    led_status = False  # LED ausschalten
            button_pressed_start_time = 0
    else:
        button_pressed_start_time = 0

    # Eine Pause einfügen, um die Abfrageintervalle anzupassen
    time.sleep(1)  # Zum Beispiel 1 Sekunde Pause zwischen den Abfragen
