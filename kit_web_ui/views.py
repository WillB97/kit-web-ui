from __future__ import annotations

import base64
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from io import BytesIO
from typing import cast

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import F
from django.http import (
    HttpRequest, HttpResponse, HttpResponsePermanentRedirect,
    HttpResponseRedirect, JsonResponse, FileResponse
)
from django.shortcuts import redirect, render, resolve_url

from .models import MqttConfig, MqttData
from .utils import get_logs, get_robot_state, get_run_data

HttpRedirect = HttpResponseRedirect | HttpResponsePermanentRedirect


def login_required_json(view_func):
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Not logged in"}, status=401)
        return view_func(request, *args, **kwargs)

    return wrapped_view


@login_required
def index(request: HttpRequest) -> HttpResponse | HttpRedirect:
    if request.user.is_staff:
        configs = MqttConfig.objects.all().annotate(
            login=F('user__username'),
            last_login=F('user__last_login'),
        )

        configs_list = [
            {
                'name': config.name,
                'username': config.login,
                'last_login': config.last_login,
                'broker': config.broker,
            }
            for config in configs
        ]

        return render(
            request,
            "team_select.html",
            {
                "now": datetime.now(timezone.utc),
                "teams": configs_list,
            },
        )
    else:
        return redirect(settings.STATIC_URL + "ui/index.html")


@login_required_json
def config(request: HttpRequest) -> JsonResponse:
    if request.user.is_staff and request.GET.get("user"):
        try:
            user = User.objects.get(username=request.GET["user"])
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
    else:
        user = cast(User, request.user)

    try:
        config: MqttConfig = user.mqtt_config
    except MqttConfig.DoesNotExist:
        return JsonResponse({"error": "User has no MQTT config"}, status=404)

    return JsonResponse({
        "django_user": user.username,
        "name": config.name,
        "broker_url": config.generate_url(),
        "topic_root": config.topic_root,
        "logout_url": resolve_url('logout'),
    })


@login_required
@staff_member_required
def view_status(request: HttpRequest) -> HttpResponse:
    states = get_robot_state()

    return render(
        request,
        "status.html",
        {
            "now": datetime.now(timezone.utc),
            "states": states,
        }
    )


@login_required
def view_runs(request: HttpRequest, user: str) -> HttpResponse:
    run_data = get_run_data(user)
    # Extract the single entry dict, accounting for it being blank
    for team_name, available_runs in run_data.items():
        break
    else:
        team_name = 'Unknown'
        available_runs = []

    runs_dict = [
        {"date": run_date, "uuid": run_uuid}
        for run_uuid, run_date in available_runs
    ]

    return render(
        request,
        "runs.html",
        {
            "now": datetime.now(timezone.utc),
            "name": team_name,
            "runs": runs_dict,
            "username": user,
        }
    )


@login_required
@staff_member_required
def run_summary(request: HttpRequest) -> HttpResponse:
    run_data = get_run_data(order_by='config__team_number')

    runs_per_day = defaultdict(lambda: defaultdict(int))
    days = set()

    for team_name, available_runs in run_data.items():
        for _run_uuid, run_date in available_runs:
            runs_per_day[team_name][run_date.date()] += 1
            days.add(run_date.date())

    return render(
        request,
        "run_summary.html",
        {
            "now": datetime.now(timezone.utc),
            "runs_by_day": {k: dict(v) for k, v in runs_per_day.items()},
            "days": sorted(days),
        }
    )


@login_required_json
def recall(request: HttpRequest, run_uuid: str) -> JsonResponse:
    if request.user.is_staff and request.GET.get("user"):
        user = request.GET['user']
    else:
        user = request.user.username

    logs = get_logs(user, run_uuid=run_uuid, end_filter=request.GET.get("end_time"))

    return JsonResponse({
        "logs": logs,
        "camera": MqttData.objects.filter(
            subtopic='camera/annotated',
            run_uuid=run_uuid,
            config__user__username=user,
        ).values_list('payload', flat=True).latest()
    })


@login_required
def get_run_logs(request: HttpRequest, run_uuid: str) -> HttpResponse:
    if request.user.is_staff and request.GET.get("user"):
        user = request.GET['user']
    else:
        user = request.user.username

    logs = get_logs(user, run_uuid=run_uuid, end_filter=request.GET.get("end_time"))
    log_lines = [
        log['message']
        for log in logs
    ]

    base_query = MqttData.objects.filter(run_uuid=run_uuid, config__user__username=user)

    log_date = (
        base_query
        .filter(subtopic='state')
        .values_list('date', flat=True)
        .last()
    )
    if log_date:
        filename = f"log-{log_date:%Y-%m-%dT%H-%M-%S}.txt"
    else:
        filename = "log.txt"

    response = HttpResponse('\n'.join(log_lines), content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response


@login_required
def generate_run_bundle(request: HttpRequest, run_uuid: str) -> FileResponse:
    # zip file with log.txt and jpgs
    if request.user.is_staff and request.GET.get("user"):
        user = request.GET['user']
    else:
        user = request.user.username

    base_query = MqttData.objects.filter(run_uuid=run_uuid, config__user__username=user)

    # create log.txt
    logs = get_logs(user, run_uuid=run_uuid, end_filter=request.GET.get("end_time"))
    log_lines = [log['message'] for log in logs]

    log_date = (
        base_query
        .filter(subtopic='state')
        .values_list('date', flat=True)
        .last()
    )
    if log_date:
        filename = f"logs-{user}-{log_date:%Y-%m-%dT%H-%M-%S}.zip"
    else:
        filename = f"logs-{user}.txt"

    byte_data = BytesIO()
    with zipfile.ZipFile(byte_data, "w", zipfile.ZIP_DEFLATED, False) as output_file:
        # write the log to the zip
        output_file.writestr('log.txt', '\n'.join(log_lines))

        # Save all images as jpegs
        for img in base_query.filter(subtopic='camera/annotated'):
            # Remove the data:image/jpeg;base64, prefix
            img_txt = img.payload['data'].split()[-1]

            img_data = base64.b64decode(img_txt)

            output_file.writestr(f'img-{img.date:%Y-%m-%dT%H-%M-%S}-.jpg', img_data)

    # If you don't return the buffer to the start, nothing will appear in the response
    byte_data.seek(0)

    return FileResponse(
        byte_data,
        content_type='application/zip',
        as_attachment=True,
        filename=filename
    )