from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.db.models import Q
from django.template.loader import render_to_string
from django.urls import reverse
import django.contrib.messages as messages
import members.models
from shifts.models import *
import datetime

from shifter.settings import MAIN_PAGE_HOME_BUTTON


def prepare_default_context(contextToAdd):
    """
    providing any of the following will override their default values:
    @defaultDate   now
    @latest_revision  last created with valid status
    @APP_NAME   name of the APP displayed in the upper left corner
    """
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
    revisions = Revision.objects.filter(valid=True).order_by("-number")
    if "GET" == request.method:
        revision = revisions.first()
    else:
        revision = Revision.objects.filter(number=request.POST['revision']).first()
    scheduled_shifts = Shift.objects.filter(revision=revision).order_by('date', 'slot__hour_start',
                                                                        'member__role__priority')
    scheduled_campaigns = Campaign.objects.filter(revision=revision)
    context = {
        'revisions': revisions,
        'displayed_revision': revision,
        'scheduled_shifts_list': scheduled_shifts,
        'scheduled_campaigns_list': scheduled_campaigns,
    }
    return render(request, 'index.html', prepare_default_context(context))


def dates(request):
    context = {
        'campaigns': Campaign.objects.all(),
        'slots': Slot.objects.all(),
        'shiftroles': ShiftRole.objects.all(),
        'memberroles': members.models.Role.objects.all(),
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


# TODO provide user based view/ (maybe with ics export) on shifts plannings
@login_required
def user(request):
    # from dateutil.relativedelta import relativedelta
    currentMonth = datetime.datetime.now()
    nextMonth = currentMonth + datetime.timedelta(30) # banking rounding
    member = request.user
    revision = Revision.objects.filter(valid=True).order_by("-number").first()
    scheduled_shifts = Shift.objects.filter(member=member, revision=revision)
    scheduled_campaigns = Campaign.objects.all()
    context = {
        'member' : member,
        'currentmonth':currentMonth.strftime('%B'),
        'nextmonth': nextMonth.strftime('%B'),
        'scheduled_shifts_list': scheduled_shifts,
        'scheduled_campaigns_list': scheduled_campaigns,
    }
    return render(request, 'user.html', prepare_default_context(context))


@login_required
def icalendar_view(request):

    # TODO get those from the GET request
    month = None
    monthLabel = request.GET.get('month')
    if request.GET.get('month'):
        if monthLabel=='current':
            month = datetime.datetime.now()
        if monthLabel == 'next':
            month = datetime.datetime.now() + datetime.timedelta(30)
    member = None
    if request.GET.get('member'):
        member = Member.objects.filter(id=request.GET.get('member')).first()

    if month is None or member is None:
        # TODO render error page
        pass

    monthFirstDay = month.replace(day=1).date()
    next_month = monthFirstDay.replace(day=28) + datetime.timedelta(days=4)
    monthLastDay = next_month.replace(day=1) + datetime.timedelta(days=-1)

    campaign = Campaign.objects.filter(name='TS2 Ops').first()
    revision = Revision.objects.filter(valid=True).order_by("-number").first()

    shifts = Shift.objects.filter(date__lte=monthLastDay, date__gte=monthFirstDay)\
                          .filter(member=member, campaign=campaign, revision=revision)
    context = {
        'campaign': campaign,
        'shifts': shifts,
        'member': member,
    }
    body = render_to_string('icalendar.ics', context)
    # Note iCalendar format requires CR/LF line endings
    return HttpResponse(body.replace('\n', '\r\n'), content_type='text/calendar')


@login_required
def ioc_update(request):
    # TODO WIP_IOC used for testing
    # TODO WIP_IOC see the EPICS integrations options for the IOC (maybe only read is needed)
    # TODO send a slack webhook announcement
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

    revision = Revision.objects.filter(number=request.POST['revision']).first()
    campaign = Campaign.objects.filter(id=request.POST['camp']).first()
    defautshiftrole = None
    if int(request.POST['role']) > 0:
        defautshiftrole = ShiftRole.objects.filter(id=request.POST['role']).first()
    shiftRole = defautshiftrole
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
            nameFromFile = fields[0]
            for dayIndex, one in enumerate(fields):
                if dayIndex == 0:
                    continue
                if one == '' or one == '-': # neutral shift slot abbrev
                    continue
                slotAbbrev = one
                shiftDetais = one.split(':')
                if len(shiftDetais): # index 0-> name, index -> shift role
                    slotAbbrev = shiftDetais[0]
                    if len(shiftDetais) > 1:
                        if shiftDetais[1] == "-":
                            shiftRole = None
                        else:
                            shiftRole = ShiftRole.objects.filter(abbreviation=shiftDetais[1]).first()
                            if shiftRole is None:
                                messages.error(request, 'Cannot find role defined like {} for at line \
                                                            {} and column {} (for {}), using default one {}.'\
                                                        .format(shiftDetais[1], lineIndex, dayIndex,
                                                                nameFromFile, defautshiftrole))
                                shiftRole = defautshiftrole

                shiftFullDate = date + datetime.timedelta(days=dayIndex - 1)
                shift = Shift()
                try:
                    member = Member.objects.get(first_name=nameFromFile)
                    slot = Slot.objects.get(abbreviation=slotAbbrev)
                    shift.campaign = campaign
                    shift.role = shiftRole
                    shift.revision = revision
                    shift.date = shiftFullDate
                    shift.slot = slot
                    shift.member = member
                    shift.csv_upload_tag = csv_file.name
                    totalLinesAdded += 1
                except Exception:
                    messages.error(request, 'Could not find system member for ({}) / slot ({}), in line {} column {}.\
                                    Skipping for now Check your file'
                                   .format(fields[0], one, lineIndex, dayIndex))
                try:
                    shift.save()
                    shiftRole = defautshiftrole
                except Exception:
                    messages.error(request, 'Could not add member {} for {} {}, \
                                            Already in the system for the same \
                                            role: {}  campaign: {} and revision {}'
                                            .format(member, shiftFullDate, one, shiftRole, campaign, revision))

    except Exception as e:
        messages.error(request, "Unable to upload file. Critical error, see {}".format(e))

    messages.success(request, "Uploaded and saved {} shifts provided with {}".format(totalLinesAdded, csv_file.name))
    return HttpResponseRedirect(reverse("shifter:shift-upload"))
