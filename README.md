
<h1 align="center">
  <br>
  <a href="http://honeyguard.schoepf-tirol.at"><img src="https://honeyguard.schoepf-tirol.at/img/Logo.png" alt="HoneyGuard" width="300"></a>
  <br>
  Markdownify
  <br>
</h1>

# HoneyGuard Installation

This guide will help you install and configure HoneyGuard on your Raspberry Pi.

## Prerequisites

Make sure you have the following components connected to your Raspberry Pi:
- A/D Converter (HX711) for load cells:
    - VCC to Pin 02/5V (preferably a 3.3V pin)
    - GND to Pin 06/Ground
    - DT to Pin 29/GPIO5
    - SCK to Pin 31/GPIO6
- Temperature sensors (DS18B20) for the incubator:
    - VCC to Pin 17/3.3V
    - GND to Pin 14/Ground
    - GPIO11
- Environmental sensor (BME680) for temperature, humidity, pressure, and air quality:
    - VCC to Pin 04/5V
    - GND to Pin 09/Ground
    - SCK to Pin 05/SCL
    - SDI to Pin 03/SDA
- Button for switching between maintenance and measurement mode:
    - Pin 01/3.3V
    - GPIO16

Also, make sure that you have an InfluxDB and Grafana instance set up.

## Installation Steps

1. Update and upgrade your Raspberry Pi:
    ```bash
    sudo apt-get update
    sudo apt-get upgrade -y
    ```

2. Install the required packages and libraries:
    ```bash
    sudo apt-get install -y python3-pip git i2c-tools influxdb jq
    sudo pip3 install RPi.GPIO influxdb bme680
    ```

3. Clone the HX711 library repository and install it:
    ```bash
    git clone https://github.com/tatobari/hx711py.git
    cd hx711py
    sudo python3 setup.py install
    cd ..
    ```

4. Clone the HoneyGuard repository:
    ```bash
    git clone https://github.com/Zenutrix/HoneyGuard.git
    ```

5. Enable the I2C interface:
    ```bash
    sudo raspi-config nonint do_i2c 0
    ```

6. Configure the HoneyGuard service:
    ```bash
    sudo cp HoneyGuard/honeyguard.service /etc/systemd/system/
    sudo systemctl enable honeyguard.service
    sudo systemctl start honeyguard.service
    ```

7. Create the InfluxDB database and user:
    ```bash
    influx -execute "CREATE DATABASE honeyguard"
    influx -execute "CREATE USER honeyguard WITH PASSWORD 'your_password' WITH ALL PRIVILEGES"
    ```

8. Update the HoneyGuard configuration:
    - Open the `HoneyGuard/config.json` file.
    - Update the InfluxDB host, port, database, user, and password.
    - Save the changes.

9. Start the InfluxDB and Grafana services:
    ```bash
    sudo systemctl start influxdb
    sudo systemctl enable influxdb
    sudo systemctl start grafana-server
    sudo systemctl enable grafana-server
    ```

10. Access the Grafana dashboard:
    - Open a web browser and enter your Raspberry Pi's IP address followed by port `3000` (e.g., `http://<raspberry_pi_ip_address>:3000`).
    - Log in with the default credentials (username: `admin`, password: `admin`).
    - Follow the Grafana setup wizard to set a new password and configure data sources.

11. You're ready to use HoneyGuard! Make sure all the sensors are properly connected and monitor your beekeeping environment.

## Usage

- The HoneyGuard service will start automatically on boot and continuously monitor the sensors.
- Use the button connected to GPIO16 to switch between maintenance and measurement modes.
- The measured data will be stored in the InfluxDB database and can be visualized using the Grafana dashboard.

## Troubleshooting

If you encounter any issues during the installation or usage of HoneyGuard, please refer to the [HoneyGuard GitHub repository](https://github.com/Zenutrix/HoneyGuard) for troubleshooting guidance.


