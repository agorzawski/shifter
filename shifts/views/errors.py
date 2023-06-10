from django.shortcuts import render


def page_not_found(request, exception):
    return render(request, "404.html", {})


def error_500(request):
    return render(request, '500.html', {})
