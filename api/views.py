from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from .permissions import is_auditor


@login_required
def home(request):
    return render(request, 'api/index.html', {'read_only': is_auditor(request.user) and not request.user.is_superuser})


def health(request):
    return JsonResponse({'status': 'ok'})
