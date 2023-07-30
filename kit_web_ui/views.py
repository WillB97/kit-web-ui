from datetime import datetime, timezone

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def index(request):
    return render(request, "base.html", {"now": datetime.now(timezone.utc)})
