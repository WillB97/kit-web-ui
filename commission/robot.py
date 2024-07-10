"""
Commisioning script for a for Wi-Fi and MQTT on a sourcebots robot.

Values are read from the CSV file using the Wi-Fi MAC address to select the relevant details.
"""
import csv
import os
from pathlib import Path
from tempfile import TemporaryDirectory


DETAILs_FILE = Path(__file__).parent / 'details.csv'
ROBOT_WIFI_PASSWORD = "00000000"
MQTT_HOST = "kit-ui.local"


def lookup_device_details(mac_addr):
    all_configs = {}
    with open(DETAILs_FILE, 'r') as f:
        csv_reader = csv.DictReader(f)
        for row in csv_reader:
            all_configs[row['mac_addr'].lower()] = row

    return all_configs.get(mac_addr.lower(), {})


def provision(mac_addr):
    dev_details = lookup_device_details(mac_addr)
    # create a temporary directory to generate the files in
    with TemporaryDirectory() as tmpdirname:
        tmpdir = Path(tmpdirname)
        # write the mqtt config
        with open(tmpdir / 'mqtt.conf', 'w') as f:
            f.writelines([
                '{\n',
                f'    "host": "{MQTT_HOST}",\n',
                '    "port": 8883,\n',
                f'    "topic_prefix": "{dev_details.get("username", "")}",\n',
                '    "use_tls": true,\n',
                f'    "username": "{dev_details.get("username", "")}",\n',
                f'    "password": "{dev_details.get("mqtt_password", "")}"\n',
                '}\n',
            ])

        # configure the network
        if wifi_password := dev_details.get("wifi_password"):
            os.system('sudo nmcli connection add type wifi ifname wlan0 con-name SOTON-IoT ssid SOTON-IoT')
            os.system(f'sudo nmcli connection modify SOTON-IoT wifi-sec.key-mgmt wpa-psk wifi-sec.psk {wifi_password}')
        os.system('sudo nmcli connection add type wifi ifname wlan0 con-name robots ssid robots')
        os.system(f'sudo nmcli connection modify robots wifi-sec.key-mgmt wpa-psk wifi-sec.psk {ROBOT_WIFI_PASSWORD}')

        os.system('sudo mkdir -p /etc/sbot/')
        os.system(f'sudo mv {tmpdirname}/mqtt.conf /etc/sbot/')
        os.system('sudo reboot')


def main():
    # print available devices
    for dev in Path('/sys/class/net').iterdir():
        print(dev)
    # lookup mac addr
    mac_addr = Path('/sys/class/net/wlan0/address').read_text().strip()
    provision(mac_addr)


if __name__ == '__main__':
    main()
