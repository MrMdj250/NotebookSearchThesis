#from django.http import HttpResponse
from django.shortcuts import render
from .call import search
# base from: https://github.com/thalderg/searchsite

def search_index(request):
    results = []
    name_term = ""
    language_term = ""
    index_term = ""
    if request.GET.get('name') and request.GET.get('language') \
    and request.GET.get('index'):
        name_term = request.GET['name']
        language_term = request.GET['language']
        index_term = request.GET['index']
    elif request.GET.get('name'):
        name_term = request.GET['name']
    elif request.GET.get('language'):
        language_term = request.GET['language']
    elif request.GET.get('index'):
        index_term = request.GET['index']

    search_term = name_term or language_term
    results = search(name=name_term, language=language_term, index=index_term)

    context = {'results': results, 'count': len(results),
        'search_term': search_term}
    return render(request, 'home.html', context)
