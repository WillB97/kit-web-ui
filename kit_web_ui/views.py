from datetime import datetime, timezone

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render


@login_required
def index(request):
    return render(request, "base.html", {"now": datetime.now(timezone.utc)})


@login_required
def config(request):
    config = request.user.mqtt_config
    return JsonResponse({
        "django_user": request.user.username,
        "broker_url": config.generate_url(),
        "topic_root": config.topic_root,
    })
