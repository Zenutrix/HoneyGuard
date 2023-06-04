import subprocess

# Aktualisieren der Paketlisten für Upgrades für Pakete, die noch keine neuen Versionen haben.
subprocess.run(["sudo", "apt-get", "update"])

# Upgrade aller installierten Pakete
subprocess.run(["sudo", "apt-get", "upgrade", "-y"])

# Installieren Sie die notwendigen Pakete für den HX711 Sensor und BME680
subprocess.run(["sudo", "apt-get", "install", "-y", "python3-pip", "git", "i2c-tools", "influxdb", "jq"])

# Installieren Sie die benötigten Python-Bibliotheken
subprocess.run(["sudo", "pip3", "install", "RPi.GPIO", "influxdb", "bme680"])

# Klonen des HX711 Bibliothek Repository
subprocess.run(["git", "clone", "https://github.com/tatobari/hx711py.git"])

# Wechseln Sie in das geklonte Verzeichnis
subprocess.run(["cd", "hx711py"])

# Installieren Sie die Bibliothek
subprocess.run(["sudo", "python3", "setup.py", "install"])

# Zurück zum ursprünglichen Verzeichnis
subprocess.run(["cd", ".."])

# Fragt den Benutzer nach dem Installationsverzeichnis mit Standard als Home-Verzeichnis
install_dir = input("Geben Sie das Installationsverzeichnis ein (Standard ist $HOME): ") or "$HOME"

# Erstellen Sie das HoneyGuard Verzeichnis und wechseln Sie dorthin
subprocess.run(["mkdir", "-p", f"{install_dir}/HoneyGuard"])
subprocess.run(["cd", f"{install_dir}/HoneyGuard"])

# Klonen Sie Ihr Git Repository
subprocess.run(["git", "clone", "https://github.com/Zenutrix/HoneyGuard.git", "."])

# Aktivieren Sie die I2C-Schnittstelle auf dem Raspberry Pi
subprocess.run(["sudo", "raspi-config", "nonint", "do_i2c", "0"])

# Erstellen Sie den systemd-Dienst für Ihr Python-Skript
service_unit = f"""[Unit]
Description=HoneyGuard Service
After=multi-user.target

[Service]
ExecStart=/usr/bin/python3 {install_dir}/HoneyGuard/honeyguard.py
WorkingDirectory={install_dir}/HoneyGuard
Restart=always

[Install]
WantedBy=multi-user.target"""
with open("/etc/systemd/system/honeyguard.service", "w") as f:
    f.write(service_unit)

# Setzen Sie die Berechtigungen für den Dienst
subprocess.run(["sudo", "chmod", "644", "/etc/systemd/system/honeyguard.service"])

# Starten Sie den HoneyGuard-Dienst und stellen Sie sicher, dass er beim Booten ausgeführt wird
subprocess.run(["sudo", "systemctl", "start", "honeyguard"])
subprocess.run(["sudo", "systemctl", "enable", "honeyguard"])

# Fragt den Benutzer nach dem InfluxDB-Datenbanknamen
influxdb_db = input("Geben Sie den Namen der InfluxDB-Datenbank ein (Standard ist HoneyGuard): ") or "HoneyGuard"

# Fragt den Benutzer nach dem InfluxDB-Benutzernamen
influxdb_user = input("Geben Sie den Namen des InfluxDB-Benutzers ein (Standard ist HoneyGuard): ") or "HoneyGuard"

# Fragt den Benutzer nach dem InfluxDB-Passwort
influxdb_password = input(f"Geben Sie das Passwort für den InfluxDB-Benutzer '{influxdb_user}' ein: ")

# InfluxDB-Datenbank und -User einrichten
subprocess.run(["influx", "-execute", f"CREATE DATABASE {influxdb_db}"])
subprocess.run(["influx", "-execute", f"CREATE USER {influxdb_user} WITH PASSWORD '{influxdb_password}' WITH ALL PRIVILEGES"])

# Aktualisieren Sie die config.json mit den InfluxDB-Einstellungen
import json
config_file = f"{install_dir}/HoneyGuard/config.json"
with open(config_file, "r") as f:
    config = json.load(f)

config["influx"]["db"] = influxdb_db
config["influx"]["user"] = influxdb_user
config["influx"]["password"] = influxdb_password

with open(config_file, "w") as f:
    json.dump(config, f)

# Starten Sie den InfluxDB-Dienst
subprocess.run(["sudo", "systemctl", "unmask", "influxdb.service"])
subprocess.run(["sudo", "systemctl", "start", "influxdb"])
subprocess.run(["sudo", "systemctl", "enable", "influxdb"])

# Installieren Sie Grafana
subprocess.run(["wget", "-q", "-O", "-", "https://packages.grafana.com/gpg.key", "|", "sudo", "apt-key", "add", "-"])
subprocess.run(["echo", "'deb https://packages.grafana.com/oss/deb stable main'", "|", "sudo", "tee", "/etc/apt/sources.list.d/grafana.list"])
subprocess.run(["sudo", "apt-get", "update"])
subprocess.run(["sudo", "apt-get", "install", "-y", "grafana"])

# Starten Sie den Grafana-Dienst und stellen Sie sicher, dass er beim Booten ausgeführt wird
subprocess.run(["sudo", "systemctl", "start", "grafana-server"])
subprocess.run(["sudo", "systemctl", "enable", "grafana-server"])

print("Installation abgeschlossen.")
