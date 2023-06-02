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

# Fragt den Benutzer nach dem Installationsverzeichnis mit Standard als Home-Verzeichnis
read -p "Geben Sie das Installationsverzeichnis ein (Standard ist $HOME): " install_dir
install_dir=${install_dir:-$HOME}

# Erstellen Sie das HoneyGuard Verzeichnis und wechseln Sie dorthin
mkdir -p $install_dir/HoneyGuard
cd $install_dir/HoneyGuard

# Klonen Sie Ihr Git Repository
git clone https://github.com/Zenutrix/HoneyGuard.git .

# Aktivieren Sie die I2C-Schnittstelle auf dem Raspberry Pi
sudo raspi-config nonint do_i2c 0

# Erstellen Sie den systemd-Dienst für Ihr Python-Skript
echo "[Unit]
Description=HoneyGuard Service
After=multi-user.target

[Service]
ExecStart=/usr/bin/python3 $install_dir/HoneyGuard/honeyguard.py
WorkingDirectory=$install_dir/HoneyGuard
Restart=always

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/honeyguard.service

# Setzen Sie die Berechtigungen für den Dienst
sudo chmod 644 /etc/systemd/system/honeyguard.service

# Starten Sie den HoneyGuard-Dienst und stellen Sie sicher, dass er beim Booten ausgeführt wird
sudo systemctl start honeyguard
sudo systemctl enable honeyguard

# Fragt den Benutzer nach dem InfluxDB-Datenbanknamen
read -p "Geben Sie den Namen der InfluxDB-Datenbank ein (Standard ist HoneyGuard): " influxdb_db
influxdb_db=${influxdb_db:-HoneyGuard}

# Fragt den Benutzer nach dem InfluxDB-Benutzernamen
read -p "Geben Sie den Namen des InfluxDB-Benutzers ein (Standard ist HoneyGuard): " influxdb_user
influxdb_user=${influxdb_user:-HoneyGuard}

# Fragt den Benutzer nach dem InfluxDB-Passwort
read -s -p "Geben Sie das Passwort für den InfluxDB-Benutzer '$influxdb_user' ein: " influxdb_password
echo

# InfluxDB-Datenbank und -User einrichten
influx -execute "CREATE DATABASE $influxdb_db"
influx -execute "CREATE USER $influxdb_user WITH PASSWORD '$influxdb_password' WITH ALL PRIVILEGES"

# Aktualisieren Sie die config.json mit den InfluxDB-Einstellungen
jq ".influx.db = \"$influxdb_db\" |
    .influx.user = \"$influxdb_user\" |
    .influx.password = \"$influxdb_password\"" $install_dir/HoneyGuard/config.json > tmp.$$.json && mv tmp.$$.json $install_dir/HoneyGuard/config.json

# Starten Sie den InfluxDB-Dienst
sudo systemctl unmask influxdb.service
sudo systemctl start influxdb
sudo systemctl enable influxdb

# Installieren Sie Grafana
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt-get update
sudo apt-get install -y grafana

# Starten Sie den Grafana-Dienst und stellen Sie sicher, dass er beim Booten ausgeführt wird
sudo systemctl start grafana-server
sudo systemctl enable grafana-server

echo "Installation abgeschlossen."
