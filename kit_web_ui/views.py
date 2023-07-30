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
        return render(
            request,
            "team_select.html",
            {
                "now": datetime.now(timezone.utc),
                "teams": MqttConfig.objects.all(),
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
        "base.html",  # TODO: Change this to the actual UI
        {
            "broker_url": config.generate_url(),
            "topic_root": config.topic_root,
        },
    )
