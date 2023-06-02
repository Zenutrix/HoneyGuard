#!/bin/bash

# Aktualisieren der Paketlisten für Upgrades für Pakete, die noch keine neuen Versionen haben.
sudo apt-get update

# Upgrade aller installierten Pakete
sudo apt-get upgrade -y

# Installieren Sie die notwendigen Pakete für den HX711 Sensor und BME680
sudo apt-get install -y python3-pip git i2c-tools influxdb jq

# Installieren Sie die benötigten Python-Bibliotheken
sudo pip3 install RPi.GPIO influxdb bme680

# Klonen des HX711 Bibliothek Repository
git clone https://github.com/tatobari/hx711py.git

# Wechseln Sie in das geklonte Verzeichnis
cd hx711py

# Installieren Sie die Bibliothek
sudo python3 setup.py install

# Zurück zum ursprünglichen Verzeichnis
cd ..

# Klonen Sie Ihr Git Repository
git clone https://github.com/your-username/your-repository.git

# Aktivieren Sie die I2C-Schnittstelle auf dem Raspberry Pi
sudo raspi-config nonint do_i2c 0

# Erstellen Sie den systemd-Dienst für Ihr Python-Skript
echo "[Unit]
Description=HoneyGuard Service
After=multi-user.target

[Service]
ExecStart=/usr/bin/python3 /path/to/honeyguard.py
WorkingDirectory=/path/to
Restart=always

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/honeyguard.service

# Ersetzen Sie "/path/to/honeyguard.py" und "/path/to" mit dem Pfad zu Ihrem Skript und dem Arbeitsverzeichnis

# Setzen Sie die Berechtigungen für den Dienst
sudo chmod 644 /etc/systemd/system/honeyguard.service

# Starten Sie den HoneyGuard-Dienst und stellen Sie sicher, dass er beim Booten ausgeführt wird
sudo systemctl start honeyguard
sudo systemctl enable honeyguard

# Aktualisieren Sie die config.json mit den InfluxDB-Einstellungen
jq '.influx.host = "127.0.0.1" |
    .influx.port = 8086 |
    .influx.db = "yourdb" |
    .influx.user = "yourusername" |
    .influx.password = "yourpassword"' config.json > tmp.$$.json && mv tmp.$$.json config.json

# Starten Sie den InfluxDB-Dienst
sudo systemctl unmask influxdb.service
sudo systemctl start influxdb
sudo systemctl enable influxdb

echo "Installation abgeschlossen."
