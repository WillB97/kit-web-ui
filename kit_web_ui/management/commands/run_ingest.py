"""
Save received MQTT data to the database.

This script connects to the MQTT broker using the configuration from the Django settings file.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Dict

    import paho.mqtt.client as mqtt

    from kit_web_ui.models import MqttConfig

from django.core.management.base import BaseCommand

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Save received MQTT data to the database'
    topic_root_mapping: Dict[str, MqttConfig] = {}

    def handle(self, *args, **options) -> None:  # type: ignore
        import paho.mqtt.client as mqtt
        from django.conf import settings
        from kit_web_ui.models import MqttConfig

        # Prepopulate mapping of topic root to MqttConfig
        # to avoid querying the database for each message
        self.topic_root_mapping = MqttConfig.objects.in_bulk(field_name='topic_root')

        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            protocol=mqtt.MQTTProtocolVersion.MQTTv5,
        )

        if settings.MQTT_BROKER['USE_TLS']:
            client.tls_set()
            if settings.MQTT_BROKER['USE_TLS'] == 'insecure':
                client.tls_insecure_set(True)

        if settings.MQTT_BROKER['username']:
            client.username_pw_set(
                settings.MQTT_BROKER['USERNAME'],
                settings.MQTT_BROKER['PASSWORD'],
            )

        client.on_connect = self._on_connect
        client.on_message = self._on_message

        client.connect(
            host=settings.MQTT_BROKER['HOST'],
            port=settings.MQTT_BROKER['PORT'],
        )

        client.loop_forever()
        self.stdout.write("Done")

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        connect_flags: mqtt.ConnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties | None = None,
    ) -> None:
        if reason_code.is_failure:
            LOGGER.warning(
                "Failed to connect to MQTT broker. "
                f"Return code: {reason_code.getName()}"  # type: ignore[no-untyped-call] # noqa: E501
            )
        else:

            LOGGER.debug("Connected to MQTT broker.")
            # Subscribe to all topics
            client.subscribe("#")

    def _on_message(
        self,
        client: mqtt.Client,
        userdata: Any,
        message: mqtt.MQTTMessage,
    ) -> None:
        import json
        from kit_web_ui.models import MqttData

        try:
            payload = json.loads(message.payload)
        except json.JSONDecodeError:
            LOGGER.warning("Failed to decode message on topic %s: %b", message.topic, message.payload)
            return

        # Extract the topic root from the message topic
        message_config = None
        subtopic = message.topic
        for topic_root, config in self.topic_root_mapping.items():
            if message.topic.startswith(topic_root):
                message_config = config
                subtopic = message.topic[len(topic_root):]
                break

        # Attempt to extract timestamp from the message payload
        timestamp = payload.get('timestamp', message.timestamp)

        # Save the message to the database
        MqttData.objects.create(
            date=timestamp,
            config=message_config,
            subtopic=subtopic,
            payload=payload,
            run_uuid=payload.get('run_uuid', ''),
        )
