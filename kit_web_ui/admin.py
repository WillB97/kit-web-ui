from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin

from .models import AuditEvent, Broker, BrokerListener, MqttConfig, MqttData
from .utils import generate_password, generate_wordlist


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
    list_display = ("team_number", "name", "user", "broker", "username", "topic_root", "generate_full_url")
    list_filter = ("user", "broker", "topic_root")
    search_fields = ("name", "user__username", "broker__name", "broker__broker__host")


class MqttDataAdmin(admin.ModelAdmin):
    list_display = ("date", "config", "run_uuid", "subtopic", "payload")
    list_filter = ("date", "run_uuid", "subtopic")
    search_fields = ("run_uuid", "config__name", "subtopic")


class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("date", "user", "action", "code", "extra_data", "target_other")
    list_filter = ("date", "user", "action", "code")
    search_fields = ("name", "user__username", "broker__name", "extra_data__ip")


@admin.action(description="Enable selected users")
def make_active(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description="Disable selected users")
def make_inactive(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.action(description="Regenerate selected users passwords")
def regenerate_passwords(modeladmin: admin.ModelAdmin, request, queryset):
    if settings.KIT_UI['WORDLIST']:
        wordlist = generate_wordlist(settings.KIT_UI['WORDLIST'])
    else:
        wordlist = None

    for user in queryset:
        new_password = generate_password(wordlist)

        # update password
        user.set_password(new_password)
        user.save()

        # print the password in the admin interface
        modeladmin.message_user(
            request,
            f"Password for {user} set to {new_password}.",
            messages.INFO
        )


UserAdmin.actions = [*UserAdmin.actions, make_active, make_inactive, regenerate_passwords]
admin.site.register(Broker, BrokerAdmin)
admin.site.register(BrokerListener, BrokerListenerAdmin)
admin.site.register(MqttConfig, MqttConfigAdmin)
admin.site.register(MqttData, MqttDataAdmin)
admin.site.register(AuditEvent, AuditEventAdmin)
