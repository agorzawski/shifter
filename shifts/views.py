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
import os

from shifter.settings import MAIN_PAGE_HOME_BUTTON, APP_REPO, APP_REPO_ICON, CONTROL_ROOM_PHONE_NUMBER, WWW_EXTRA_INFO,\
    SHIFTER_PRODUCTION_INSTANCE, SHIFTER_TEST_INSTANCE

DATE_FORMAT = '%Y-%m-%d'
DATE_FORMAT_SLIM = '%Y%m%d'


def prepare_default_context(request, contextToAdd):
    """
    providing any of the following will override their default values:
    @defaultDate   now
    @latest_revision  last created with valid status
    @APP_NAME   name of the APP displayed in the upper left corner
    """
    date = datetime.datetime.now().date()
    latest_revision = Revision.objects.filter(valid=True).order_by('-number').first()
    stream = os.popen('git describe --tags')
    GIT_LAST_TAG = stream.read()
    print(SHIFTER_TEST_INSTANCE)
    if SHIFTER_TEST_INSTANCE:
        messages.info(request, 'This is an test instance. Please refer to <a href="{}">the production instance</a> for uptodate schedule.'.format(SHIFTER_PRODUCTION_INSTANCE),)
    for oneShifterMessages in ShifterMessage.objects.filter(valid=True).order_by('-number'):
        messages.warning(request, oneShifterMessages.description)
    context = {
        'logged_user': request.user.is_authenticated,
        'defaultDate': date.strftime(DATE_FORMAT),
        'slots': Slot.objects.all().order_by('hour_start'),
        'latest_revision': latest_revision,
        'displayed_revision': latest_revision,
        'APP_NAME': MAIN_PAGE_HOME_BUTTON,
        'APP_REPO': APP_REPO,
        'APP_REPO_ICON': APP_REPO_ICON,
        'APP_GIT_TAG': GIT_LAST_TAG,
        'controlRoomPhoneNumber': CONTROL_ROOM_PHONE_NUMBER,
        'wwwWithMoreInfo': WWW_EXTRA_INFO,
    }
    for one in contextToAdd.keys():
        context[one] = contextToAdd[one]
    return context


def prepareShiftId(today, activeSlot):
    shiftMap = {0: 'A', 1: 'B', 3: 'C', -1: 'X'}
    # TODO consider extracting that as config
    opSlots = Slot.objects.filter(op=True).order_by('hour_start')
    number = -1
    for idx, item in enumerate(opSlots):
        if item == activeSlot:
            number = idx
    return today.strftime(DATE_FORMAT_SLIM) + shiftMap[number]


def prepare_active_crew(request, dayToGo=None, slotToGo=None):
    import members.directory as directory
    ldap = directory.LDAP()
    today = datetime.datetime.now()
    now = today.time()
    if dayToGo is not None and slotToGo is not None:
        today = datetime.datetime.strptime(dayToGo, DATE_FORMAT)
        now = Slot.objects.filter(abbreviation=slotToGo).first().hour_start

    revision = Revision.objects.filter(valid=True).order_by("-number").first()
    scheduled_shifts = Shift.objects.filter(date=today).filter(revision=revision)
    slots = []
    for slot in Slot.objects.all():
        if slot.hour_start <= now < slot.hour_end:
            for shifter in scheduled_shifts:
                if shifter.slot == slot:
                    slots.append(slot)
    activeSlot = Slot.objects.first()
    activeSlots = []
    currentTeam = []
    for slot in set(slots):
        if slot.hour_start <= now < slot.hour_end:
            for shifter in scheduled_shifts:
                if shifter.slot == slot:
                    activeSlot = slot
                    activeSlots.append(slot)
                    currentTeam.append(shifter)
                    # print('Check details for {}'.format(shifter.member.last_name))
                    personal_data = ldap.search(field='name', text=shifter.member.last_name)
                    if len(personal_data) == 0:
                        continue
                    one = list(personal_data.keys())[0]
                    if len(personal_data) > 1:
                        for oneK in personal_data.keys():
                            if shifter.member.last_name.lower() in oneK.lower() \
                                    and shifter.member.first_name.lower() in oneK.lower():
                                one = oneK

                    # Temporary assignment from the LDAP, for the purpose of the render,
                    # NOT TO BE persisted, i.e. do not use shifter.save()!
                    shifter.member.email = personal_data[one]['email']
                    shifter.member.mobile = personal_data[one]['mobile']
                    if type(personal_data[one]['photo']) is not str:
                        import base64
                        shifter.member.photo = base64.b64encode(personal_data[one]['photo']).decode("utf-8")

    return {'today': today,
            'shiftID': prepareShiftId(today, activeSlot),
            'activeSlots': set(activeSlots),
            'activeSlot': activeSlot,
            'currentTeam': currentTeam}


def index(request):
    revisions = Revision.objects.filter(valid=True).order_by("-number")
    if "GET" == request.method:
        revision = revisions.first()
    else:
        revision = Revision.objects.filter(number=request.POST['revision']).first()
        # TODO implement filter on campaigns

    scheduled_shifts = Shift.objects.filter(revision=revision).order_by('date', 'slot__hour_start',
                                                                        'member__role__priority')
    scheduled_campaigns = Campaign.objects.filter(revision=revision)
    context = {
        'revisions': revisions,
        'displayed_revision': revision,
        'scheduled_shifts_list': scheduled_shifts,
        'scheduled_campaigns_list': scheduled_campaigns,
    }
    return render(request, 'index.html', prepare_default_context(request, context))


def dates(request):
    context = {
        'campaigns': Campaign.objects.all(),
        'slots': Slot.objects.all(),
        'shiftroles': ShiftRole.objects.all(),
        'memberroles': members.models.Role.objects.all(),
    }
    return render(request, 'dates.html', prepare_default_context(request, context))


def todays(request):
    dayToGo = request.GET.get('date', None)
    slotToGo = request.GET.get('slot', None)
    activeShift = prepare_active_crew(request, dayToGo=dayToGo, slotToGo=slotToGo)
    context = {'today': activeShift['today'],
               'activeSlots': activeShift['activeSlots'],
               'currentTeam': activeShift['currentTeam'],
               'shiftID': activeShift['shiftID'],}
    return render(request, 'today.html', prepare_default_context(request, context))


@login_required
def user(request):
    currentMonth = datetime.datetime.now()
    nextMonth = currentMonth + datetime.timedelta(30) # banking rounding
    member = request.user
    revision = Revision.objects.filter(valid=True).order_by("-number").first()
    scheduled_shifts = Shift.objects.filter(member=member, revision=revision)
    scheduled_campaigns = Campaign.objects.all().filter(revision=revision)
    context = {
        'member': member,
        'currentmonth': currentMonth.strftime('%B'),
        'nextmonth': nextMonth.strftime('%B'),
        'scheduled_shifts_list': scheduled_shifts,
        'scheduled_campaigns_list': scheduled_campaigns,
    }
    return render(request, 'user.html', prepare_default_context(request, context))


@login_required
def icalendar_view(request):
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
    revision = Revision.objects.filter(valid=True).order_by("-number").first()

    shifts = Shift.objects.filter(date__lte=monthLastDay, date__gte=monthFirstDay)\
                          .filter(member=member, revision=revision)
    context = {
        'campaign': 'Exported Shifts',
        'shifts': shifts,
        'member': member,
    }
    body = render_to_string('icalendar.ics', context)
    # Note iCalendar format requires CR/LF line endings
    return HttpResponse(body.replace('\n', '\r\n'), content_type='text/calendar')


def ioc_update(request):
    """
    Expose JSON with current shift setup. To be used by any script/tool to update the IOC
    """
    dayToGo = request.GET.get('date', None)
    slotToGo =  request.GET.get('slot', None)
    # TODO WIP send a slack webhook announcement to remind that this was called
    fieldsToUpdate = ['SL', 'OP', 'OCC', 'OC', 'OCE', 'OCPSS']
    # TODO add separate call for OC updates + separate url
    fieldsToUpdate = ['SL', 'OP']
    activeShift = prepare_active_crew(request, dayToGo=dayToGo, slotToGo=slotToGo)
    # TODO maybe define a sort of config file to avoid having it hardcoded here, for now not crutial
    dataToReturn = {'_datetime': activeShift['today'].strftime(DATE_FORMAT),
                    '_slot': activeShift['activeSlot'].abbreviation,
                    '_PVPrefix': 'NSO:Ops:',
                    'SID': activeShift['shiftID'],
                    }
    for one in fieldsToUpdate:
        dataToReturn[one] = "N/A"
    for one in fieldsToUpdate:
        for shifter in activeShift['currentTeam']:
            if one in shifter.member.role.abbreviation:
                dataToReturn[one] = shifter.member.name
                dataToReturn[one + "Phone"] = shifter.member.mobile
                dataToReturn[one + "Email"] = shifter.member.email
    return JsonResponse(dataToReturn)


@login_required
def shifts_update(request):
    # add campaigns and revisions
    data = {'campaigns': Campaign.objects.all(),
            'revisions': Revision.objects.all(),
            'today': datetime.datetime.now().strftime(DATE_FORMAT)
            }

    totalLinesAdded = 0
    if "GET" == request.method:
        return render(request, "shifts_update.html", prepare_default_context(request, data))

    else:
        revision = Revision.objects.filter(number=request.POST['revision']).first()
        campaign = Campaign.objects.filter(id=request.POST['camp']).first()
        oldStartDate = campaign.date_start
        newStartDate = datetime.datetime.strptime(request.POST['new-date'], DATE_FORMAT).date()
        daysDelta = newStartDate - oldStartDate
        deltaToApply = datetime.timedelta(days=daysDelta.days)
        messages.info(request, 'Found {} difference to update'.format(daysDelta))
        shifts_to_update = Shift.objects.filter(campaign=campaign, revision=campaign.revision)
        messages.info(request, 'Found {} shifts to update'.format(len(shifts_to_update)))
        doneCounter = 0
        for oldShift in shifts_to_update:
            shift = Shift()
            shift.member = oldShift.member
            shift.campaign = campaign
            shift.slot = oldShift.slot
            shift.role = oldShift.role
            tag = oldShift.csv_upload_tag
            if tag is None:
                tag = ""
            shift.csv_upload_tag = tag + '_update'
            # updated info
            shift.revision = revision
            shift.date = oldShift.date + deltaToApply
            try:
                shift.save()
                doneCounter +=1
            except Exception:
                messages.error(request, 'Cannot update old shift {}, skipping!'.format(oldShift))

        # at last, update the actual campaign data
        campaign.revision = revision
        campaign.date_start = campaign.date_start + deltaToApply
        campaign.date_end =  campaign.date_end + deltaToApply
        campaign.save()
        messages.info(request, 'Done OK with {} shifts'.format(doneCounter))
        return HttpResponseRedirect(reverse("shifter:shift-update"))


@login_required
def shifts_upload(request):
    # add campaigns and revisions

    data = {'campaigns': Campaign.objects.all(),
            'revisions': Revision.objects.all(),
            'roles' : ShiftRole.objects.all(),
            }

    totalLinesAdded = 0
    if "GET" == request.method:
        return render(request, "shifts_upload.html", prepare_default_context(request, data))

    # POST
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
