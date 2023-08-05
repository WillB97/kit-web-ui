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
        with open(tmpdir / 'wpa_supplicant.conf', 'w') as f:
            f.writelines([
                'ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n',
                'update_config=1\n',
                'country=GB\n',
                '\n',
                'network={\n',
                '    ssid="SOTON-IOT"\n',
                f'    psk="{dev_details.get("wifi_password", "00000000")}"\n',
                '    key_mgmt=WPA-PSK\n',
                '}\n',
                '\n',
                'network={\n',
                '    ssid="robots"\n',
                f'    psk="{ROBOT_WIFI_PASSWORD}>"\n',
                '    key_mgmt=WPA-PSK\n',
                '}\n',
            ])
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

        os.system(f'sudo mv {tmpdirname}/wpa_supplicant.conf /boot/')
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
