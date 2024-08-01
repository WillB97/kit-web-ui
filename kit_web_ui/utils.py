from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from secrets import choice
from string import ascii_letters, digits

from django.db.models import Min, F, OuterRef, Subquery

from kit_web_ui.models import MqttData


def generate_wordlist(word_file: str | Path) -> list[str]:
    with open(word_file) as wordlist:
        return [
            clean_word.lower()
            for word in wordlist
            if len(clean_word := word.strip()) > 4
            and len(clean_word) < 10
            and clean_word.isalpha()
        ]


def generate_password(wordlist: list[str] | None = None) -> str:
    if wordlist:
        return '-'.join(choice(wordlist) for _ in range(2))
    else:
        return ''.join(choice(ascii_letters + digits) for _ in range(12))


def get_run_data() -> dict[str, list[tuple[str, datetime]]]:
    run_data = (
        MqttData.objects
        .filter(subtopic='state', payload__state__exact='Running')
        .values(
            'run_uuid',
            team_name=F('config__name'),
        )
        .annotate(start=Min('date'))
    )

    runs = defaultdict(list)

    for run_val in run_data:
        runs[run_val['team_name']].append((run_val['run_uuid'], run_val['start']))

    return dict(runs)

def get_robot_state():
    newest_state = MqttData.objects.filter(config=OuterRef("id"), subtopic='state')
    newest_connected = MqttData.objects.filter(config=OuterRef("id"), subtopic='connected')

    MqttData.objects.annotate(
        latest_state=Subquery(newest_state.values("payload__state")[:1]),
        latest_connected=Subquery(newest_connected.values("payload__connected")[:1]),
    ).values('name', 'latest_state', 'latest_connected')
