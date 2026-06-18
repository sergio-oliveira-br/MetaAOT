# webapp/views.py

from django.http import HttpResponse

def index(request):
    return HttpResponse("<h1>MetaAOT</h1><p>Primeira página funcionando.</p>")
