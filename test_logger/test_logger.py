#!/usr/bin/env python3
import argparse
import json
import logging
import sys
from itertools import count
from pathlib import Path
from time import sleep, time

import paho.mqtt.client as mqtt

IMAGE_DATA = []
PROGRESS_COUNT = 0


def progress(indicator):
    global PROGRESS_COUNT
    print(indicator, end="")
    sys.stdout.flush()

    PROGRESS_COUNT += 1
    if PROGRESS_COUNT > 80:
        PROGRESS_COUNT = 0
        print()


class MQTT():
    def __init__(self, host, port=1883, use_tls=False, username='', password=''):
        self.mqtt = mqtt.Client()

        if use_tls:
            self.mqtt.tls_set()
            if use_tls == 'insecure':
                self.mqtt.tls_insecure_set(True)

        if username:
            self.mqtt.username_pw_set(username, password)

        try:
            self.mqtt.connect(host=host, port=port, keepalive=60)
        except (TimeoutError, ValueError, ConnectionRefusedError):
            print(f"Failed to connect to MQTT broker at {host}:{port}")
            return
        self.mqtt.loop_start()

    def __del__(self) -> None:
        self.mqtt.disconnect()
        self.mqtt.loop_stop()

    def publish(self, topic, payload, qos=0, retain=False):
        self.mqtt.publish(topic, payload, qos=qos, retain=retain)


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    parser = argparse.ArgumentParser(
        description="""
        MQTT test publisher
        Publishes test log messages once per second and test images every 10
        seconds to the specified MQTT broker.
        """)
    parser.add_argument('--host', default='localhost', help='MQTT broker host')
    parser.add_argument('--port', default=1883, type=int, help='MQTT broker port')
    parser.add_argument('--use-tls', default=False, action='store_true', help='Use TLS')
    parser.add_argument(
        '--insecure', default=False, action='store_true', help='Allow insecure TLS')
    parser.add_argument('--username', default='', help='MQTT username')
    parser.add_argument('--password', default='', help='MQTT password')
    parser.add_argument('--topic-root', default='test', help='MQTT topic root to publish to')

    args = parser.parse_args()

    # load images
    for i in range(1, 6):
        IMAGE_DATA.append(
            (Path(__file__).parent / f'img-{i:02d}.jpg.txt').read_text(encoding='utf-8')
        )

    mqtt = MQTT(args.host, args.port, args.use_tls, args.username, args.password)

    try:
        mqtt.publish(
            f'{args.topic_root}/connected', '{"state": "connected"}', qos=1, retain=True)
        mqtt.mqtt.will_set(
            f'{args.topic_root}/connected', '{"state": "disconnected"}', qos=1, retain=True)
        for i in count():
            mqtt.publish(f'{args.topic_root}/logs', json.dumps(
                {
                    "timestamp": time(), "message": f"[{i:04d}.259] Test Message",
                    "raw_message": "Test Message", "level": "USERCODE", "name": "usercode"
                }))
            progress('l')
            if i % 10 == 0:
                progress('i')
                # publish image
                image = (i // 10) % len(IMAGE_DATA)
                mqtt.publish(f'{args.topic_root}/camera/annotated', json.dumps({"data": IMAGE_DATA[image]}))
            sleep(1)
    except KeyboardInterrupt:
        mqtt.publish(
            f'{args.topic_root}/connected', '{"state": "disconnected"}', qos=1, retain=True)


if __name__ == '__main__':
    main()
