
<h1 align="center">
  <br>
  <a href="http://honeyguard.schoepf-tirol.at"><img src="https://honeyguard.schoepf-tirol.at/img/Logow.png" alt="HoneyGuard" width="300"></a>
</h1>

## Support

<a href="https://buymeacoffee.com/thomas.austria" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/purple_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>

# HoneyGuard Installation Guide

This guide will walk you through the steps to install HoneyGuard on a Raspberry Pi. HoneyGuard is a monitoring system that captures weight and temperature data using a load cell (HX711), temperature sensors (DS18B20), and an environmental sensor (BME680), and stores the data in an InfluxDB database.

## Prerequisites

- Raspberry Pi with Raspbian or a compatible operating system
- Internet connection

## Installation Steps

1. **Prepare the Raspberry Pi**
   - Make sure your Raspberry Pi is properly set up and connected to the internet.
   - Open a terminal on your Raspberry Pi.

2. **Download the Installation Script**
   - Run the following command to download the installation script:
     ```
     wget https://raw.githubusercontent.com/Zenutrix/HoneyGuard/main/setup.py
     ```

3. **Run the Installation Script**
   - Give execution permission to the installation script with the following command:
     ```
     sudo python3 setup.py
     ```

4. **Enter Configuration Settings**
     ```
     sudo nano /home/pi/Honeyguard/config.json
     ```
   - Edit Database Name what you want.
   - Edit Tare
   - Edit GPO Pins you want or Default
   - 
     - 

5. **Complete the Installation**
   - The installation script will install the required packages, configure the system, and set up the HoneyGuard service.
   - Once the installation is complete, start HoneyGuard by running the following command:
     ```
     sudo systemctl start honeyguard
     ```

   - To ensure that HoneyGuard starts automatically on system boot, run the following command:
     ```
     sudo systemctl enable honeyguard
     ```

6. **Verify the Installation**
   - Monitor HoneyGuard by viewing the log file:
     ```
     sudo journalctl -u honeyguard -f
     ```

   - Check the database connection by logging in to InfluxDB:
     ```
     influx
     ```

   - To customize the HoneyGuard configuration, edit the `config.json` file located in the HoneyGuard installation directory.

7. **HoneyGuard Features**
   - HoneyGuard captures weight and temperature data from the load cell and DS18B20 temperature sensors.
   - It also measures environmental parameters such as temperature, humidity, pressure, and air quality using the BME680 sensor.
   - The data is stored in an InfluxDB database, allowing you to analyze and visualize the data.
   - For visualizing the data, you can use Grafana, a powerful open-source platform for data visualization.
   - Set up Grafana by accessing the Grafana web interface and configuring it to connect to your InfluxDB database.

Congratulations! You have successfully installed HoneyGuard. The system should now capture weight, temperature, and environmental data and store it in the InfluxDB database. You can explore and visualize the data using Grafana and other compatible tools.

For more information and advanced usage, please refer to the HoneyGuard documentation.

Enjoy monitoring your environment with HoneyGuard!
