from django.shortcuts import render

from django.http import HttpResponse

from shifts.models import *

import datetime
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


def todays(request):
    today = datetime.datetime(2021,3,23)
    now = datetime.datetime.now().time()

    scheduled_shifts = Shift.objects.filter(date=today)
    print(scheduled_shifts)

    slots = Slot.objects.all()

    currentTeam = []
    for slot in slots:
        if now > slot.hour_start  and now < slot.hour_end:
            for shifter in scheduled_shifts:
                if shifter.slot == slot:
                    activeSlot = slot
                    currentTeam.append(shifter)

    print(currentTeam)
    context ={'today': today,
              'activeSlot':activeSlot,
              'currentTeam': currentTeam}

    return render(request, 'today.html', context)
