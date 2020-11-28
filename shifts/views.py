from django.shortcuts import render

from django.http import HttpResponse

from shifts.models import *

# def index(request):
#     return HttpResponse("Hello, world. You will see lots of shitfs here")

def index(request):
    scheduled_shifts = Shift.objects.all()
    scheduled_campaigns = Campaign.objects.all()
    #template = loader.get_template('planning/index.html')
    context = {
        'scheduled_shifts_list': scheduled_shifts,
        'scheduled_campaigns_list':scheduled_campaigns
    }
    return render(request, 'index.html', context)


def user(request):
    scheduled_shifts = Shift.objects.all()
    scheduled_campaigns = Campaign.objects.all()
    #template = loader.get_template('planning/index.html')
    context = {
        'scheduled_shifts_list': scheduled_shifts,
        'scheduled_campaigns_list':scheduled_campaigns
    }
    return render(request, 'index.html', context)
