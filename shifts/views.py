from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.db.models import Q, Count
from django.template.loader import render_to_string
from django.urls import reverse
import django.contrib.messages as messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods, require_safe

import members.models
from shifts.models import *
import datetime
import os
import phonenumbers

from shifter.settings import MAIN_PAGE_HOME_BUTTON, APP_REPO, APP_REPO_ICON, CONTROL_ROOM_PHONE_NUMBER, WWW_EXTRA_INFO, \
    SHIFTER_PRODUCTION_INSTANCE, SHIFTER_TEST_INSTANCE, PHONEBOOK_NAME

DATE_FORMAT = '%Y-%m-%d'
DATE_FORMAT_SLIM = '%Y%m%d'
MONTH_NAME = '%B'


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
    if SHIFTER_TEST_INSTANCE:
        messages.info(request,
                      'This is an test instance. Please refer to <a href="{}">the production instance</a> for uptodate schedule.'.format(
                          SHIFTER_PRODUCTION_INSTANCE), )
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
        'PHONEBOOK_NAME': PHONEBOOK_NAME,
        'APP_GIT_TAG': GIT_LAST_TAG,
        'controlRoomPhoneNumber': CONTROL_ROOM_PHONE_NUMBER,
        'wwwWithMoreInfo': WWW_EXTRA_INFO,
    }
    for one in contextToAdd.keys():
        context[one] = contextToAdd[one]
    return context


def prepareShiftId(today, activeSlot):
    shiftMap = {0: 'A', 1: 'B', 2: 'C', -1: 'X'}
    # TODO consider extracting that as config
    opSlots = Slot.objects.filter(op=True).order_by('hour_start')
    number = -1
    for idx, item in enumerate(opSlots):
        if item == activeSlot:
            number = idx
    return today.strftime(DATE_FORMAT_SLIM) + shiftMap[number]


def filter_active_slots(now, scheduled_shifts, slotsToConsider):
    slots = []
    for slot in slotsToConsider:
        if (slot.hour_start > slot.hour_end and (slot.hour_start <= now or now < slot.hour_end)) \
                or slot.hour_start <= now < slot.hour_end:
            for shifter in scheduled_shifts:
                if shifter.slot == slot:
                    slots.append(slot)
    return slots


def prepare_active_crew(request, dayToGo=None, slotToGo=None, onlyOP=False):
    import members.directory as directory
    ldap = directory.LDAP()
    today = datetime.datetime.now()
    now = today.time()
    # now = datetime.datetime(2021, 6, 29, 3, 12, 00).time()
    # TODO fix the date switch when probing the current shift
    #  but day after like 29/06 at 3:00 should still give ID for one started at 28/06..
    if dayToGo is not None and slotToGo is not None:
        today = datetime.datetime.strptime(dayToGo, DATE_FORMAT)
        now = Slot.objects.filter(abbreviation=slotToGo).first().hour_start

    revision = Revision.objects.filter(valid=True).order_by("-number").first()
    scheduled_shifts = Shift.objects.filter(date=today).filter(revision=revision)
    slotsToConsider = Slot.objects.all() if not onlyOP else Slot.objects.filter(op=True)
    slots = filter_active_slots(now, scheduled_shifts, slotsToConsider)
    slotsOPWithinScheduled = filter_active_slots(now, scheduled_shifts, Slot.objects.filter(op=True))
    slotToBeUsed = None
    if len(slotsOPWithinScheduled) == 0:
        slotsOPWithinScheduled = slots
        # FIXME check when off 24h slots
    else:
        slotToBeUsed = slotsOPWithinScheduled[0]

    def takeHourEnd(slotToSort):
        return slotToSort.hour_end

    sortedSlots = list(set(slots))
    sortedSlots.sort(key=takeHourEnd)
    activeSlot = Slot.objects.first()
    activeSlots = []
    currentTeam = []
    for slot in sortedSlots:
        if (slot.hour_start > slot.hour_end and (slot.hour_start <= now or now < slot.hour_end)) \
                or slot.hour_start <= now < slot.hour_end:
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
                    shifter.member.mobile = 'N/A'
                    try:
                        pn = phonenumbers.parse(personal_data[one]['mobile'])
                        shifter.member.mobile = phonenumbers.format_number(pn,
                                                                           phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                    except Exception:
                        pass
                    if type(personal_data[one]['photo']) is not str:
                        import base64
                        shifter.member.photo = base64.b64encode(personal_data[one]['photo']).decode("utf-8")

    return {'today': today,
            'shiftID': prepareShiftId(today, slotToBeUsed),
            'activeSlots': set(activeSlots),
            'activeSlot': slotToBeUsed,
            'currentTeam': currentTeam}


@require_safe
def index(request):
    revisions = Revision.objects.filter(valid=True).order_by("-number")
    revision = revisions.first()
    return prepare_main_page(request, revisions, revision)


@require_http_methods(["POST"])
@csrf_protect
def index_post(request):
    revisions = Revision.objects.filter(valid=True).order_by("-number")
    revision = Revision.objects.filter(number=request.POST['revision']).first()
    # TODO implement filter on campaigns
    filtered_campaigns = None
    return prepare_main_page(request, revisions, revision, filtered_campaigns=filtered_campaigns)


def prepare_main_page(request, revisions, revision, filtered_campaigns=None):
    scheduled_shifts = Shift.objects.filter(revision=revision).order_by('date', 'slot__hour_start',
                                                                        'member__role__priority')
    scheduled_campaigns = Campaign.objects.filter(revision=revision)
    context = {
        'revisions': revisions,
        'displayed_revision': revision,
        'scheduled_shifts_list': scheduled_shifts,
        'filtered_campaigns': filtered_campaigns,
        'scheduled_campaigns_list': scheduled_campaigns,
    }
    return render(request, 'index.html', prepare_default_context(request, context))


@require_safe
def dates(request):
    context = {
        'campaigns': Campaign.objects.all(),
        'slots': Slot.objects.all(),
        'shiftroles': ShiftRole.objects.all(),
        'memberroles': members.models.Role.objects.all(),
    }
    return render(request, 'dates.html', prepare_default_context(request, context))


@require_safe
def todays(request):
    dayToGo = request.GET.get('date', None)
    slotToGo = request.GET.get('slot', None)
    activeShift = prepare_active_crew(request, dayToGo=dayToGo, slotToGo=slotToGo)
    context = {'today': activeShift['today'],
               'checkTime': activeShift['today'].time(),
               'activeSlots': activeShift['activeSlots'],
               'currentTeam': activeShift['currentTeam'],
               'shiftID': activeShift['shiftID'], }
    return render(request, 'today.html', prepare_default_context(request, context))


@require_safe
@login_required
def user(request):
    currentMonth = datetime.datetime.now()
    nextMonth = currentMonth + datetime.timedelta(30)  # banking rounding
    member = request.user
    revision = Revision.objects.filter(valid=True).order_by("-number").first()
    scheduled_shifts = Shift.objects.filter(member=member, revision=revision)
    scheduled_campaigns = Campaign.objects.all().filter(revision=revision)
    context = {
        'member': member,
        'currentmonth': currentMonth.strftime(MONTH_NAME),
        'nextmonth': nextMonth.strftime(MONTH_NAME),
        'scheduled_shifts_list': scheduled_shifts,
        'scheduled_campaigns_list': scheduled_campaigns,
    }
    return render(request, 'user.html', prepare_default_context(request, context))


def get_shift_summary(m, validSlots, revision, currentMonth) -> tuple:
    scheduled_shifts = Shift.objects.filter(member=m,
                                            revision=revision,
                                            date__year=currentMonth.year,
                                            date__month=currentMonth.month)

    differentSlots = Shift.objects.filter(member=m,
                                          revision=revision,
                                          date__year=currentMonth.year,
                                          date__month=currentMonth.month) \
        .values('slot__abbreviation') \
        .annotate(total=Count('slot'))

    result = {a['slot__abbreviation']: a['total'] for a in differentSlots}
    return len(scheduled_shifts), result


@require_safe
@login_required
def team(request):
    currentMonth = datetime.datetime.now()
    if request.GET.get('date'):
        currentMonth = datetime.datetime.strptime(request.GET['date'], SIMPLE_DATE)
    nextMonth = currentMonth + datetime.timedelta(31)  # banking rounding
    lastMonth = currentMonth - datetime.timedelta(31)
    member = request.user
    teamMembers = Member.objects.filter(team=member.team)
    revision = Revision.objects.filter(valid=True).order_by("-number").first()
    scheduled_shifts = Shift.objects.filter(member__team=member.team, revision=revision)
    scheduled_campaigns = Campaign.objects.all().filter(revision=revision)
    # TODO get this outside the main code, maybe another flag in the Slot? TBC
    slotLookUp = ['NWH', 'PM', 'AM', 'EV', 'NG']
    validSlots = Slot.objects.filter(abbreviation__in=slotLookUp).order_by('hour_start')
    teamMembersSummary = []
    for m in teamMembers:
        l, result = get_shift_summary(m, validSlots, revision, currentMonth)
        memberSummary = [m, l]
        for oneSlot in validSlots:
            memberSummary.append(result.get(oneSlot.abbreviation, '--'))
        teamMembersSummary.append(memberSummary)

    context = {
        'member': member,
        'teamMembers': teamMembersSummary,
        'validSlots': validSlots,
        'currentmonth_label': currentMonth.strftime(MONTH_NAME),
        'nextmonth': nextMonth.strftime(SIMPLE_DATE),
        'lastmonth': lastMonth.strftime(SIMPLE_DATE),
        'nextmonth_label': nextMonth.strftime(MONTH_NAME),
        'lastmonth_label': lastMonth.strftime(MONTH_NAME),
        'scheduled_shifts_list': scheduled_shifts,
        'scheduled_campaigns_list': scheduled_campaigns,
    }
    return render(request, 'team.html', prepare_default_context(request, context))


@require_safe
@login_required
def icalendar_view(request):
    month = None
    monthLabel = request.GET.get('month')
    if request.GET.get('month'):
        if monthLabel == 'current':
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

    shifts = Shift.objects.filter(date__lte=monthLastDay, date__gte=monthFirstDay) \
        .filter(member=member, revision=revision)
    context = {
        'campaign': 'Exported Shifts',
        'shifts': shifts,
        'member': member,
    }
    body = render_to_string('icalendar.ics', context)
    # Note iCalendar format requires CR/LF line endings
    return HttpResponse(body.replace('\n', '\r\n'), content_type='text/calendar')


@require_safe
def ioc_update(request):
    """
    Expose JSON with current shift setup. To be used by any script/tool to update the IOC
    """
    dayToGo = request.GET.get('date', None)
    slotToGo = request.GET.get('slot', None)
    # TODO WIP send a slack webhook announcement to remind that this was called
    fieldsToUpdate = ['SL', 'OP', 'OCC', 'OC', 'OCE', 'OCPSS']
    # TODO add separate call for OC updates + separate url
    fieldsToUpdate = ['SL', 'OP']
    activeShift = prepare_active_crew(request, dayToGo=dayToGo, slotToGo=slotToGo, onlyOP=True)
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
            if one in shifter.member.role.abbreviation and shifter.role is None:  # no extra role in the same shift
                dataToReturn[one] = shifter.member.name
                dataToReturn[one + "Phone"] = shifter.member.mobile
                dataToReturn[one + "Email"] = shifter.member.email
    return JsonResponse(dataToReturn)


@require_safe
@login_required
def shifts_update(request):
    # add campaigns and revisions
    data = {'campaigns': Campaign.objects.all(),
            'revisions': Revision.objects.all(),
            'today': datetime.datetime.now().strftime(DATE_FORMAT)
            }
    return render(request, "shifts_update.html", prepare_default_context(request, data))


@require_http_methods(["POST"])
@csrf_protect
@login_required
def shifts_update_post(request):
    # add campaigns and revisions
    data = {'campaigns': Campaign.objects.all(),
            'revisions': Revision.objects.all(),
            'today': datetime.datetime.now().strftime(DATE_FORMAT)
            }

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
            doneCounter += 1
        except Exception:
            messages.error(request, 'Cannot update old shift {}, skipping!'.format(oldShift))

    # at last, update the actual campaign data
    campaign.revision = revision
    campaign.date_start = campaign.date_start + deltaToApply
    campaign.date_end = campaign.date_end + deltaToApply
    campaign.save()
    messages.info(request, 'Done OK with {} shifts'.format(doneCounter))
    return HttpResponseRedirect(reverse("shifter:shift-update"))


@require_safe
@login_required
def shifts_upload(request):
    data = {'campaigns': Campaign.objects.all(),
            'revisions': Revision.objects.all(),
            'roles': ShiftRole.objects.all(),
            }
    return render(request, "shifts_upload.html", prepare_default_context(request, data))


@require_http_methods(["POST"])
@csrf_protect
@login_required
def shifts_upload_post(request):
    # add campaigns and revisions
    data = {'campaigns': Campaign.objects.all(),
            'revisions': Revision.objects.all(),
            'roles': ShiftRole.objects.all(),
            }
    totalLinesAdded = 0
    revision = Revision.objects.filter(number=request.POST['revision']).first()
    campaign = Campaign.objects.filter(id=request.POST['camp']).first()
    defaultShiftRole = None
    if int(request.POST['role']) > 0:
        defaultShiftRole = ShiftRole.objects.filter(id=request.POST['role']).first()
    shiftRole = defaultShiftRole
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
                if one == '' or one == '-':  # neutral shift slot abbrev
                    continue
                slotAbbrev = one
                shiftDetails = one.split(':')
                if len(shiftDetails):  # index 0-> name, index -> shift role
                    slotAbbrev = shiftDetails[0]
                    if len(shiftDetails) > 1:
                        if shiftDetails[1] == "-":
                            shiftRole = None
                        else:
                            shiftRole = ShiftRole.objects.filter(abbreviation=shiftDetails[1]).first()
                            if shiftRole is None:
                                messages.error(request, 'Cannot find role defined like {} for at line \
                                                            {} and column {} (for {}), using default one {}.' \
                                               .format(shiftDetails[1], lineIndex, dayIndex,
                                                       nameFromFile, defaultShiftRole))
                                shiftRole = defaultShiftRole

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
                    shiftRole = defaultShiftRole
                except Exception:
                    messages.error(request, 'Could not add member {} for {} {}, \
                                            Already in the system for the same \
                                            role: {}  campaign: {} and revision {}'
                                   .format(member, shiftFullDate, one, shiftRole, campaign, revision))

    except Exception as e:
        messages.error(request, "Unable to upload file. Critical error, see {}".format(e))

    messages.success(request, "Uploaded and saved {} shifts provided with {}".format(totalLinesAdded, csv_file.name))
    return HttpResponseRedirect(reverse("shifter:shift-upload"))


@require_safe
def phonebook(request):
    context = {
        'result': [],
    }
    return render(request, 'phonebook.html', prepare_default_context(request, context))


@require_http_methods(["POST"])
@csrf_protect
def phonebook_post(request):
    context = {
        'result': [],
    }
    import members.directory as directory
    ldap = directory.LDAP()
    r = ldap.search(field='name', text=request.POST.get('searchKey','SomeNonsenseToNotBeFound'))
    for one in r.keys():
        photo = None
        if len(r[one]['photo']):
            import base64
            photo = base64.b64encode(r[one]['photo']).decode("utf-8")
        phoneNb = 'N/A'
        try:
            pn = phonenumbers.parse(r[one]['mobile'])
            phoneNb = phonenumbers.format_number(pn,
                                                 phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        except Exception:
            pass
        context['result'].append({'name': one,
                                  'mobile': phoneNb,
                                  'email': r[one]['email'],
                                  'photo': photo, })
    return render(request, 'phonebook.html', prepare_default_context(request, context))
