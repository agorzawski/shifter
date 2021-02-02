from django.shortcuts import render

from shifts.models import *

import datetime


def index(request):
    revision = Revision.objects.order_by("-number").first()
    scheduled_shifts = Shift.objects.filter(revision=revision).order_by('date', 'slot__hour_start', 'member__role__priority')
    print(scheduled_shifts[:3])
    scheduled_campaigns = Campaign.objects.filter(revision=revision)

    context = {
        #TODO fix the hardcoded version for debugging
        'defaultDate': '2021-04-05',
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
    #TODO remove hardcoded date for testing
    today = datetime.datetime(2021, 4, 5)
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

    #print(currentTeam)
    context ={'today': today,
              # TODO fix the hardcoded version for debugging
              'defaultDate': '2021-04-05',
              'activeSlot': activeSlot,
              'currentTeam': currentTeam}

    return render(request, 'today.html', context)
