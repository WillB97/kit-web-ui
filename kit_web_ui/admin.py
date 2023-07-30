from django.contrib import admin

from .models import Broker, BrokerListener, MqttConfig


class BrokerAdmin(admin.ModelAdmin):
    list_display = ("name", "host")
    list_filter = ("host",)
    search_fields = ("name", "host")


class BrokerListenerAdmin(admin.ModelAdmin):
    select_related = True
    list_display = ("name", "broker", "port", "protocol", "generate_url")
    list_filter = ("broker", "port", "protocol")
    search_fields = ("name", "broker__name", "broker__host")


class MqttConfigAdmin(admin.ModelAdmin):
    select_related = True
    list_display = ("name", "user", "broker", "username", "topic_root", "generate_full_url")
    list_filter = ("user", "broker", "topic_root")
    search_fields = ("name", "user__username", "broker__name", "broker__broker__host")


admin.site.register(Broker, BrokerAdmin)
admin.site.register(BrokerListener, BrokerListenerAdmin)
admin.site.register(MqttConfig, MqttConfigAdmin)
