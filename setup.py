import subprocess
import os

# Funktion zum Anzeigen des aktuellen Fortschritts
def print_status(message):
    print("\033[92m[Installation]\033[0m " + message)  # Set color to green

# Aktualisieren der Paketlisten für Upgrades für Pakete, die noch keine neuen Versionen haben.
print_status("Aktualisiere Paketlisten...")
subprocess.run(["sudo", "apt-get", "update"])

# Upgrade aller installierten Pakete
print_status("Upgrade aller installierten Pakete...")
subprocess.run(["sudo", "apt-get", "upgrade", "-y"])

# Aktiviere GPIO Pins in /boot/config.txt
print_status("Aktiviere GPIO Pins...")
with open('/boot/config.txt', 'a') as f:
    f.write('dtoverlay=w1-gpio,gpiopin=11\n')
    f.write('dtoverlay=i2c-gpio,bus=3,i2c_gpio_delay_us=1,i2c_gpio_sda=3,i2c_gpio_scl=5\n')

# Installieren der notwendigen Pakete für den HX711 Sensor und BME680
print_status("Installiere benötigte Pakete...")
subprocess.run(["sudo", "apt-get", "install", "-y", "python3-pip", "git", "i2c-tools", "influxdb", "jq"])

# Installieren der benötigten Python-Bibliotheken
print_status("Installiere benötigte Python-Bibliotheken...")
subprocess.run(["sudo", "pip3", "install", "RPi.GPIO", "influxdb", "bme680"])

# Installieren der HX711py-Bibliothek
print_status("Installiere HX711py-Bibliothek...")
subprocess.run(["sudo", "pip3", "install", "HX711py"])

# Festlegen des Installationsverzeichnisses
install_dir = "/home/pi/HoneyGuard/"

# Erstellen des HoneyGuard-Verzeichnisses und Wechseln dorthin
print_status("Erstelle HoneyGuard-Verzeichnis...")
subprocess.run(["mkdir", "-p", install_dir])
os.chdir(install_dir)

# Klonen des Git-Repositorys
print_status("Klonen des HoneyGuard-Repositorys...")
subprocess.run(["git", "clone", "https://github.com/Zenutrix/HoneyGuard.git", "."])

# Aktivieren der I2C-Schnittstelle auf dem Raspberry Pi
print_status("Aktiviere I2C-Schnittstelle...")
subprocess.run(["sudo", "raspi-config", "nonint", "do_i2c", "0"])

# Erstellen des systemd-Dienstes für das Python-Skript
print_status("Erstelle systemd-Dienst für HoneyGuard...")
service_file = f'''[Unit]
Description=HoneyGuard Service
After=multi-user.target

[Service]
ExecStart=/usr/bin/python3 {install_dir}Honeyguard.py
WorkingDirectory=/home/pi/HoneyGuard/
Restart=always

[Install]
WantedBy=multi-user.target
'''
with open('/etc/systemd/system/honeyguard.service', 'w') as f:
    f.write(service_file)

# Setzen der Berechtigungen für den Dienst
print_status("Setze Berechtigungen für den Dienst...")
subprocess.run(["sudo", "chmod", "644", "/etc/systemd/system/honeyguard.service"])

# Starten des HoneyGuard-Dienstes und Aktivieren beim Boot
#print_status("Starte HoneyGuard-Dienst und aktiviere Autostart...")
#subprocess.run(["sudo", "systemctl", "start", "honeyguard"])
#subprocess.run(["sudo", "systemctl", "enable", "honeyguard"])

# Installation von Grafana
print_status("Installiere Grafana...")
subprocess.run(["sudo", "apt-get", "update"])
subprocess.run(["sudo", "apt-get", "install", "-y", "grafana"])

# Starten von Grafana
print_status("Starte Grafana-Dienst...")
subprocess.run(["sudo", "/bin/systemctl", "start", "grafana-server"])
subprocess.run(["sudo", "/bin/systemctl", "enable", "grafana-server"])

# Abschluss der Installation
print("\033[92mErfolgreich HoneyGuard Backend installiert! :)\033[0m")
print("Sie können auf Grafana über http://<IP-Adresse des Raspberry Pi>:3000 zugreifen.")
print("Verwenden Sie die folgenden Anmeldedaten für den ersten Login:")
print("Benutzername: admin")
print("Passwort: admin")
print(" ")
print(" ")
print(" ")
print("Mache jetzt einen Neustart um die Sensoren zu Inizialisieren! sudo reboot")
