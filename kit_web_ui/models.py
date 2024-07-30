import datetime
import logging

from django.conf import settings
from django.contrib.auth import (
    user_logged_in, user_logged_out, user_login_failed,
)
from django.contrib.auth.models import User
from django.db import models
from django.dispatch import receiver


class Broker(models.Model):
    name = models.CharField(max_length=200)
    host = models.CharField(max_length=200, unique=True)

    class Meta:
        ordering = ["name"]
        default_permissions = ()

    def __str__(self) -> str:
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

    def generate_url(self) -> str:
        return f"{self.protocol}://{self.broker.host}:{self.port}"

    def __str__(self) -> str:
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
    team_number = models.IntegerField(default=100)

    class Meta:
        ordering = ["team_number", "name"]
        default_permissions = ()

    def generate_url(self) -> str:
        if not self.broker:
            return "<no broker selected>"
        else:
            return (
                f"{self.broker.protocol}://{self.username}:{self.password}@"
                f"{self.broker.broker.host}:{self.broker.port}"
            )

    def generate_full_url(self) -> str:
        return f"{self.generate_url()}/{self.topic_root}"

    def __str__(self) -> str:
        return self.name


class MqttData(models.Model):
    date = models.DateTimeField()
    config = models.ForeignKey(
        MqttConfig,
        related_name='data',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    subtopic = models.CharField(max_length=200)
    payload = models.JSONField()
    run_uuid = models.CharField(max_length=32, default="", blank=True)

    class Meta:
        ordering = ["-date"]
        default_permissions = ()

    def __str__(self) -> str:
        if self.config is None:
            return f"{self.date} {self.subtopic}"
        else:
            return f"{self.date} {self.config.topic_root}{self.subtopic}"


class AuditEvent(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="audit_events_performed",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    date = models.DateTimeField()
    target_other = models.CharField(max_length=32, null=True, blank=True)
    action = models.CharField(max_length=32)
    code = models.CharField(max_length=32)
    extra_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-date"]
        get_latest_by = ["date"]
        default_permissions = ()

    def clean(self):
        if self.extra_data is None:
            self.extra_data = {}

    def __str__(self):
        return f"{self.date} {self.user} {self.action} {self.code}"


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@receiver(user_logged_in)
def user_logged_in_callback(sender, request, user, **kwargs):
    ip = get_client_ip(request)
    AuditEvent.objects.create(
        action="login",
        user=user,
        code="succeeded",
        date=datetime.datetime.now(tz=datetime.timezone.utc),
        extra_data={"ip": ip},
    )


@receiver(user_logged_out)
def user_logged_out_callback(sender, request, user, **kwargs):
    ip = get_client_ip(request)
    AuditEvent.objects.create(
        action="logout",
        user=user,
        code="succeeded",
        date=datetime.datetime.now(tz=datetime.timezone.utc),
        extra_data={"ip": ip},
    )


@receiver(user_login_failed)
def user_login_failed_callback(sender, credentials, request, **kwargs):
    try:
        user = User.objects.get(username=credentials["username"])
    except Exception:
        logging.error(f"Login attempt for unknown user {credentials.get('username')}")
        ip = get_client_ip(request)
        AuditEvent.objects.create(
            action="login",
            target_other=credentials.get('username'),
            code="forbidden",
            date=datetime.datetime.now(tz=datetime.timezone.utc),
            extra_data={"ip": ip},
        )
    else:
        ip = get_client_ip(request)
        AuditEvent.objects.create(
            action="login",
            user=user,
            code="forbidden",
            date=datetime.datetime.now(tz=datetime.timezone.utc),
            extra_data={"ip": ip},
        )
