import subprocess
import os

# Aktualisieren der Paketlisten für Upgrades für Pakete, die noch keine neuen Versionen haben.
subprocess.run(["sudo", "apt-get", "update"])

# Upgrade aller installierten Pakete
subprocess.run(["sudo", "apt-get", "upgrade", "-y"])

# Installieren Sie die notwendigen Pakete für den HX711 Sensor und BME680
subprocess.run(["sudo", "apt-get", "install", "-y", "python3-pip", "git", "i2c-tools", "influxdb", "jq"])

# Installieren Sie die benötigten Python-Bibliotheken
subprocess.run(["sudo", "pip3", "install", "RPi.GPIO", "influxdb", "bme680"])

# Klonen des HX711-Bibliotheksrepositorys
subprocess.run(["git", "clone", "https://github.com/tatobari/hx711py.git"])

# Wechseln Sie in das geklonte Verzeichnis
os.chdir("hx711py")

# Installieren Sie die Bibliothek
subprocess.run(["sudo", "python3", "setup.py", "install"])

# Zurück zum ursprünglichen Verzeichnis
os.chdir("..")

# Festlegen des Installationsverzeichnisses
install_dir = "/home/pi/HoneyGuard/"

# Erstellen Sie das HoneyGuard-Verzeichnis und wechseln Sie dorthin
subprocess.run(["mkdir", "-p", install_dir])
os.chdir(install_dir)

# Klonen Sie Ihr Git-Repository
subprocess.run(["git", "clone", "https://github.com/Zenutrix/HoneyGuard.git", "."])

# Aktivieren Sie die I2C-Schnittstelle auf dem Raspberry Pi
subprocess.run(["sudo", "raspi-config", "nonint", "do_i2c", "0"])

# Erstellen Sie den systemd-Dienst für Ihr Python-Skript
service_file = f'''[Unit]
Description=HoneyGuard Service
After=multi-user.target

[Service]
ExecStart=/usr/bin/python3 {install_dir}honeyguard.py
WorkingDirectory={install_dir}
Restart=always

[Install]
WantedBy=multi-user.target
'''
with open('/etc/systemd/system/honeyguard.service', 'w') as f:
    f.write(service_file)

# Setzen Sie die Berechtigungen für den Dienst
subprocess.run(["sudo", "chmod", "644", "/etc/systemd/system/honeyguard.service"])

# Starten Sie den HoneyGuard-Dienst und stellen Sie sicher, dass er beim Booten ausgeführt wird
subprocess.run(["sudo", "systemctl", "start", "honeyguard"])
subprocess.run(["sudo", "systemctl", "enable", "honeyguard"])

print("Installation abgeschlossen.")
