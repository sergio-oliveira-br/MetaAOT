# webapp/views.py

from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from webapp.forms import UrlForm
@require_http_methods(["GET", "POST"])
def index(request):
    steps_log = []
    result = None
    form = UrlForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        url = form.cleaned_data['url']
        steps_log.append(f"Initiating analysis for: {url}")

    return render(request, 'index.html', {
        'form': form,
        'steps_log': steps_log,
        'result': result,
    })
