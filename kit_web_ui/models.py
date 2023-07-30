from django.conf import settings
from django.db import models


class Broker(models.Model):
    name = models.CharField(max_length=200)
    host = models.CharField(max_length=200, unique=True)

    class Meta:
        ordering = ["name"]
        default_permissions = ()

    def __str__(self):
        return f"{self.name} ({self.host})"


class BrokerListener(models.Model):
    name = models.CharField(max_length=200)
    broker = models.ForeignKey(Broker, related_name='listeners', on_delete=models.CASCADE)
    port = models.IntegerField(default=1883)
    protocol = models.CharField(max_length=10, default="mqtt", choices=(
        ("mqtt", "MQTT"),
        ("mqtts", "MQTTS"),
        ("ws", "Websocket"),
        ("wss", "Websocket Secure"),
    ))

    class Meta:
        ordering = ["name"]
        default_permissions = ()

    def generate_url(self):
        return f"{self.protocol}://{self.broker.host}:{self.port}"

    def __str__(self):
        return f"{self.name} ({self.generate_url()})"


class MqttConfig(models.Model):
    name = models.CharField(max_length=200)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, related_name='mqtt_config', on_delete=models.CASCADE)
    broker = models.ForeignKey(
        BrokerListener, related_name='user_configs', on_delete=models.SET_NULL, null=True)
    username = models.CharField(max_length=200)
    password = models.CharField(max_length=200, default="", blank=True)
    topic_root = models.CharField(max_length=200)

    class Meta:
        ordering = ["name"]
        default_permissions = ()

    def generate_url(self):
        return (
            f"{self.broker.protocol}://{self.username}:{self.password}@"
            f"{self.broker.broker.host}:{self.broker.port}"
        )

    def generate_full_url(self):
        return f"{self.generate_url()}/{self.topic_root}"

    def __str__(self):
        return self.name
