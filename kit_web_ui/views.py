from __future__ import annotations

from datetime import datetime, timezone
from typing import cast

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import (
    HttpRequest, HttpResponse, HttpResponsePermanentRedirect,
    HttpResponseRedirect, JsonResponse,
)
from django.shortcuts import redirect, render

from .models import MqttConfig

HttpRedirect = HttpResponseRedirect | HttpResponsePermanentRedirect


@login_required
def index(request: HttpRequest) -> HttpResponse | HttpRedirect:
    if request.user.is_staff:
        configs = MqttConfig.objects.all()

        # Sort teams so 10 appears after 9
        configs_list = []
        for config in configs:
            order_key_parts = []
            for part in config.name.split():
                if part.isdecimal():
                    part = f"{part:>04}"
                order_key_parts.append(part)
            order_key = '-'.join(order_key_parts)
            configs_list.append({
                'name': config.name,
                'username': config.user.username,
                'last_login': config.user.last_login,
                'broker': config.broker,
                'order_key': order_key,
            })

        configs_list.sort(key=lambda x: x['order_key'])

        return render(
            request,
            "team_select.html",
            {
                "now": datetime.now(timezone.utc),
                "teams": configs_list,
            },
        )
    else:
        return redirect("load_ui")


@login_required
@staff_member_required
def config(request: HttpRequest) -> JsonResponse:
    if request.GET.get("user"):
        try:
            user = User.objects.get(username=request.GET["user"])
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
    else:
        user = cast(User, request.user)

    try:
        config = user.mqtt_config
    except MqttConfig.DoesNotExist:
        return JsonResponse({"error": "User has no MQTT config"}, status=404)

    return JsonResponse({
        "django_user": user.username,
        "broker_url": config.generate_url(),
        "topic_root": config.topic_root,
    })


@login_required
def load_ui(request: HttpRequest) -> HttpResponse:
    if request.user.is_staff and request.GET.get("team"):
        try:
            user = User.objects.get(username=request.GET["team"])
        except User.DoesNotExist:
            user = request.user
    else:
        user = cast(User, request.user)

    try:
        config = user.mqtt_config
    except MqttConfig.DoesNotExist:
        return render(
            request,
            "base.html",
            {
                "error": "User has no MQTT config",
                "now": datetime.now(timezone.utc),
            },
        )

    return render(
        request,
        "ui.html",
        {
            "broker_url": config.generate_url(),
            "topic_root": config.topic_root,
        },
    )
