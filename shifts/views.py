from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.db.models import Q
from django.urls import reverse
import django.contrib.messages as messages

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
    data = {'datetime': today.strftime("%Y-%m-%d"), 'slot': activeSlot.abbreviation}

    for one in fieldsToUpdate:
        # TODO get actual status for now() per shift__role__abbr or shift__member__role__abbrev
        data[one] = "aaaa"
    # just return a JsonResponse
    return JsonResponse(data)


@login_required
def shifts_upload(request):
    # add campaigns and revisions

    data = {'campaigns': Campaign.objects.all(),
            'revisions': Revision.objects.all(),
            'roles' : ShiftRole.objects.all(),
            }

    totalLinesAdded = 0
    if "GET" == request.method:
        return render(request, "shifts_upload.html", prepare_default_context(data))

    print(request.POST)
    revision = Revision.objects.filter(number=request.POST['revision']).first()
    campaign = Campaign.objects.filter(id=request.POST['camp']).first()
    shiftrole = ShiftRole.objects.filter(id=request.POST['role']).first()

    try:
        csv_file = request.FILES["csv_file"]

        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Wrong file type! Needs to be CSV")
            return HttpResponseRedirect(reverse("shifter:shift-upload"))
        if csv_file.multiple_chunks():
            messages.error(request, "Too large file")
            return HttpResponseRedirect(reverse("shifter:shift-upload"))

        file_data = csv_file.read().decode("utf-8")
        date_txt = csv_file.name.replace('.csv', '').split('__')[1]
        date = datetime.datetime.fromisoformat(date_txt)

        lines = file_data.split("\n")

        for lineIndex, line in enumerate(lines):
            fields = line.split(",")
            for dayIndex, one in enumerate(fields):
                if dayIndex == 0:
                    continue
                if one == '' or one == '-':
                    continue
                shiftFullDate = date + datetime.timedelta(days=dayIndex - 1)
                shift = Shift()
                try:
                    member = Member.objects.get(first_name=fields[0])
                    slot = Slot.objects.get(abbreviation=one)
                    shift.campaign = campaign
                    shift.role = shiftrole
                    shift.revision = revision
                    shift.date = shiftFullDate
                    shift.slot = slot
                    shift.member = member
                    totalLinesAdded += 1
                except Exception:
                    messages.error(request, 'Could not find member ({}) / slot ({}), in line {} column {}. \
                                    Skipping for now Check your file'
                                   .format(fields[0], one, lineIndex, dayIndex))
                try:
                    shift.save()
                except Exception:
                    messages.error(request, 'Could not add member {} for {} {}, \
                                            Already in the system for the same \
                                            role: {}  campaign: {} and revision {}'
                                            .format(member, shiftFullDate, one, shiftrole, campaign, revision))

    except Exception as e:
        messages.error(request, "Unable to upload file. Critical error, see {}".format(e))

    messages.success(request, "Uploaded and saved {} shifts".format(totalLinesAdded))
    return HttpResponseRedirect(reverse("shifter:shift-upload"))
