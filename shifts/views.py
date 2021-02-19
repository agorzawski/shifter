from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Q
from shifts.models import *

import datetime

from shifter.settings import MAIN_PAGE_HOME_BUTTON


def prepare_default_context(contextToAdd):
    date = datetime.datetime.now().date()
    latest_revision = Revision.objects.filter(valid=True).order_by('-number').first()
    context = {
        'defaultDate': date.strftime("%Y-%m-%d"),
        'latest_revision': latest_revision,
        'APP_NAME': MAIN_PAGE_HOME_BUTTON,
    }
    for one in contextToAdd.keys():
        context[one] = contextToAdd[one]
    return context


def index(request):
    revision = Revision.objects.filter(valid=True).order_by("-number").first()
    scheduled_shifts = Shift.objects.filter(revision=revision).order_by('date', 'slot__hour_start',
                                                                        'member__role__priority')
    print(scheduled_shifts[:3])
    scheduled_campaigns = Campaign.objects.filter(revision=revision)

    context = {
        'scheduled_shifts_list': scheduled_shifts,
        'scheduled_campaigns_list': scheduled_campaigns
    }
    return render(request, 'index.html', prepare_default_context(context))


# TODO provide user based view/ (maybe with ics export) on shifts plannings
# def user(request):
#     scheduled_shifts = Shift.objects.all()
#     scheduled_campaigns = Campaign.objects.all()
#     context = {
#         'scheduled_shifts_list': scheduled_shifts,
#         'scheduled_campaigns_list': scheduled_campaigns
#     }
#     return render(request, 'index.html', prepare_default_context(context))


def dates(request):
    context = {
        'campaigns': Campaign.objects.all(),
        'slots': Slot.objects.all(),
    }
    return render(request, 'dates.html', prepare_default_context(context))


def todays(request):

    import members.directory as directory
    ldap = directory.LDAP()

    today = datetime.datetime.now()
    now = today.time()
    revision = Revision.objects.filter(valid=True).order_by("-number").first()
    scheduled_shifts = Shift.objects.filter(date=today).filter(revision=revision)

    slots = Slot.objects.all()
    activeSlot = slots[0]
    currentTeam = []
    for slot in slots:
        if slot.hour_start < now < slot.hour_end:
            for shifter in scheduled_shifts:
                if shifter.slot == slot:
                    activeSlot = slot
                    currentTeam.append(shifter)
                    print('Check details for {}'.format(shifter.member.last_name))
                    personal_data = ldap.search(field='name', text=shifter.member.last_name)
                    if len(personal_data) > 0:
                        print(personal_data)

    context = {'today': today,
               'activeSlot': activeSlot,
               'currentTeam': currentTeam}
    return render(request, 'today.html', prepare_default_context(context))


def ioc_update(request):
    fieldsToUpdate = ['SL', 'OP', 'OCC', 'OC', 'OCE', 'OCPSS']
    today = datetime.datetime.now()
    now = today.time()
    slots = Slot.objects.filter(~Q(abbreviation='NWH'))
    activeSlot = slots[0]
    for slot in slots:
        if slot.hour_start < now < slot.hour_end:
            activeSlot = slot
    data = {'datetime':today.strftime("%Y-%m-%d"), 'slot':activeSlot.abbreviation}

    for one in fieldsToUpdate:
        # TODO get actual status for now() per shift__role__abbr or shift__member__role__abbrev
        data[one] = "aaaa"
    # just return a JsonResponse
    return JsonResponse(data)
