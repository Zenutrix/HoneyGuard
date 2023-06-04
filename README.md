<h1 align="center">
  <br>
  <a href="http://honeyguard.schoepf-tirol.at"><img src="https://honeyguard.schoepf-tirol.at/img/Logow.png" alt="HoneyGuard" width="300"></a>
</h1>

## Unterstützung

<a href="https://buymeacoffee.com/thomas.austria" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/purple_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>

# Was ist Honeyguard

Das Hauptziel von HoneyGuard besteht darin, eine umfassende Überwachungslösung für Bienenvölker bereitzustellen. Durch die Integration verschiedener Sensoren wie Gewichtssensoren, Temperatursensoren und Luftqualitätssensoren ermöglicht HoneyGuard Imkern, wichtige Informationen über ihre Bienenstöcke zu sammeln. Diese Daten können helfen, den Zustand der Bienenstöcke zu überwachen, Anomalien zu erkennen und rechtzeitig Maßnahmen zu ergreifen, um die Gesundheit und das Wohlbefinden der Bienen zu gewährleisten.

## Was braucht man ?

- Raspberry Pi (3,4)
- Internet Verbindung für die Einrichtung
- HX711 
  - Wägezelle H30A
- DS18B20 (Temperatur Sensor) bis zu 30 am gleichen Bus
- Adafruit BME680 (Sensor für Temperatur, Luftfeuchtigkeit, Luftdruck und VOC / Gassensoren)
- Widerstände

## Einkaufsliste

Besuchen Sie unsere [Website](http://honeyguard.schoepf-tirol.at) für eine vollständige Einkaufsliste mit den benötigten Komponenten.

## Installations-Schritte

1. **Raspberry Pi vorbereiten**
- Stellen Sie sicher, dass Ihr Raspberry Pi ordnungsgemäß eingerichtet ist und eine Verbindung zum Internet hat.

2. **Herunterladen der Setup.py**
   - Lade zuerst die Installationsdatei herunter.
     ```
     wget https://raw.githubusercontent.com/Zenutrix/HoneyGuard/main/setup.py
     ```

3. **Installation durchführen**
   - Grafana GPG KEY:
    ```
     wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
    ```
    - Grafana REPO:
    ```
     echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
     ```
    - HoneyGuard Installation:
     ```
     sudo python3 setup.py
     ```
    - Neustart:
     ```
     sudo reboot
     ```

4. **Status von HoneyGuard überprüfen**
     ```
     sudo systemctl status honeyguard
     ```

5. **HoneyGuard-Dienst starten/Status anzeigen**
   - Das Installations-Skript installiert die erforderlichen Pakete, konfiguriert das System und richtet den HoneyGuard-Dienst ein.
   - Sobald die Installation abgeschlossen ist, starten Sie HoneyGuard mit dem folgenden Befehl:
     ```
     sudo systemctl start honeyguard
     ```

   - Um die HoneyGuard-Konfiguration anzupassen, bearbeiten Sie die Datei `config.json`, die sich im HoneyGuard-Installationsverzeichnis befindet.

7. **HoneyGuard-Konfiguration anpassen**

   - Um die HoneyGuard-Konfiguration anzupassen, bearbeiten Sie die Datei `config.json`, die sich im HoneyGuard-Installationsverzeichnis befindet.

Viel Spaß mit der Überwachung Ihrer Bienen mit HoneyGuard!

