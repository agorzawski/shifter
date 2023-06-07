from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404, Http404, redirect
from django.core.exceptions import PermissionDenied

from django.template.loader import render_to_string
from django.urls import reverse
import django.contrib.messages as messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods, require_safe
from django.db import IntegrityError
from django.db.models import Q
from django.views import View

import members.models
from members.models import Team
from shifts.models import *
from assets.models import *
from studies.models import *
from assets.forms import AssetBookingForm, AssetBookingFormClosing
import datetime
import phonenumbers
from shifts.activeshift import prepare_active_crew, prepare_for_JSON
from shifts.contexts import prepare_default_context, prepare_user_context
from shifter.settings import DEFAULT_SHIFT_SLOT
from shifts.workinghours import find_daily_rest_time_violation, find_weekly_rest_time_violation, find_working_hours

from django.utils import timezone


@require_safe
def index(request, team_id=-1):
    revisions = Revision.objects.filter(valid=True).order_by("-number")
    team = None
    if team_id > 0:
        team = get_object_or_404(Team, id=team_id)
    return prepare_main_page(request, revisions, team)


@login_required
def my_team(request):
    revisions = Revision.objects.filter(valid=True).order_by("-number")
    team = request.user.team
    return prepare_main_page(request, revisions, team, my_team=True)


def prepare_main_page(request, revisions, team, revision=None, filtered_campaigns=None, all_roles=False, my_team=False):
    if revision is None:
        revision = revisions.first()
    someDate = datetime.datetime.now() + datetime.timedelta(days=-61)  # default - always last two months
    scheduled_campaigns = Campaign.objects.filter(revision=revision).filter(date_end__gt=someDate)
    if filtered_campaigns is not None:
        scheduled_campaigns = Campaign.objects.filter(revision=revision).filter(id__in=filtered_campaigns)
    months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    month_as_int = datetime.datetime.now().month
    previous_month_as_int = months[months.index(month_as_int) - 1]
    next_month_as_int = months[months.index(month_as_int) + 1]
    context = {
        'revisions': revisions,
        'displayed_revision': revision,
        'campaigns': Campaign.objects.filter(revision=revision),
        'scheduled_campaigns_list': scheduled_campaigns,
        'all_roles': all_roles,
        'team': team,
        'my_team': my_team,
        'shift_slots': [] if not my_team else Slot.objects.filter(used_for_lookup=True).order_by('hour_start'),
        'current_month': [-1, ""] if not my_team else [month_as_int,
                                                       datetime.date(1900, month_as_int, 1).strftime('%B')],
        'previous_month': [-1, ""] if not my_team else [previous_month_as_int,
                                                        datetime.date(1900, previous_month_as_int, 1).strftime('%B')],
        'next_month': [-1, ""] if not my_team else [next_month_as_int,
                                                    datetime.date(1900, next_month_as_int, 1).strftime('%B')]
    }
    return render(request, 'team_view.html', prepare_default_context(request, context))


@require_safe
def dates(request):
    context = {
        'campaigns': Campaign.objects.all(),
        'slots': Slot.objects.all().order_by('hour_start'),
        'shiftroles': ShiftRole.objects.all(),
        'memberroles': members.models.Role.objects.all(),
        'assets': Asset.objects.all()
    }
    return render(request, 'dates.html', prepare_default_context(request, context))


@login_required
@require_http_methods(["POST"])
@csrf_protect
def dates_slots_update(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    count = 0
    for slot in Slot.objects.all():
        slot.op = False
        toUpdate = request.POST.get(slot.abbreviation, None)
        if toUpdate is not None:
            slot.op = True
            count = + 1
            messages.success(request, "Slot {} is operational now!".format(slot))
        slot.save()
    if count == 0:
        s = Slot.objects.filter(abbreviation=DEFAULT_SHIFT_SLOT).first()
        s.op = True
        s.save()
        messages.success(request, "There must be at leasst one slot set to operational, setting default {} ".format(s))
    return HttpResponseRedirect(reverse("shifter:dates"))


@require_safe
def todays(request):
    dayToGo = request.GET.get('date', None)
    slotToGo = request.GET.get('slot', None)
    hourToGo = request.GET.get('hour', None)
    fullUpdate = request.GET.get('fullUpdate', None) is not None
    activeShift = prepare_active_crew(dayToGo=dayToGo,
                                      slotToGo=slotToGo,
                                      hourToGo=hourToGo,
                                      fullUpdate=fullUpdate)
    todayAM = datetime.datetime.today().replace(hour=0, minute=0, second=1, microsecond=0)
    todayPM = datetime.datetime.today().replace(hour=23, minute=59, second=00, microsecond=0)
    scheduled_studies = StudyRequest.objects.filter(state__in=["B", "D"], slot_start__gte=todayAM,
                                                    slot_end__lte=todayPM).order_by('slot_start', 'priority')
    context = {'today': activeShift['today'],
               'checkTime': activeShift['today'].time(),
               'activeSlot': activeShift['activeSlot'],
               'activeSlots': activeShift['activeSlots'],
               'currentTeam': activeShift['currentTeam'],
               'shiftID': activeShift['shiftID'],
               'activeStudies': scheduled_studies}
    nowShift = None
    for one in activeShift['currentTeam']:
        nowShift = one
    if nowShift is not None:
        nextTeam = Shift.objects.filter(revision=nowShift.revision,
                                        date=nowShift.end,
                                        slot__hour_start=nowShift.slot.hour_end)
        nextSlot = None
        for one in nextTeam:
            nextSlot = one.slot
        if nextSlot is not None:
            context['nextSlot'] = nextSlot
            context['nextTeam'] = nextTeam
    return render(request, 'today.html', prepare_default_context(request, context))


@require_safe
@login_required
def user(request, u=None, rid=None):
    if u is None:
        member = request.user
    else:
        member = Member.objects.filter(id=u).first()

    today = datetime.datetime.now()
    year = today.year
    month = today.month

    default_start = datetime.date(year, month, 1)
    default_end = datetime.date(year, month + 1, 1) + datetime.timedelta(days=-1)
    context = prepare_user_context(member, revisionNext=rid)
    context['revisions'] = Revision.objects.order_by('-number')
    context['default_start'] = default_start
    context['default_end'] = default_end
    context['hide_campaign_selection'] = True
    context['hide_extra_role_selection'] = True
    context['show_companion'] = True
    context['the_url'] = reverse('ajax.get_user_events')
    if rid is not None:
        requested_revision = get_object_or_404(Revision, number=rid)
        revision = Revision.objects.filter(valid=True).order_by("-number").first()
        if requested_revision not in Revision.objects.filter(date_start__gt=revision.date_start).filter(
                ready_for_preview=True).filter(merged=False).order_by("-number"):
            raise Http404
        messages.warning(request,
                         "On top of the current schedule, you're seeing revision '{}'".format(requested_revision))
        context['requested_future_rev_id'] = rid

    return render(request, 'user.html', prepare_default_context(request, context))


@login_required()
def users(request):
    # Requesting all ACTIVES user, but anonymous
    first_name = Q(first_name__exact='')
    last_name = Q(last_name__exact='')
    users_list = Member.objects.filter(is_active=True).exclude(first_name & last_name)
    users_requested = request.GET.get('u', '')
    users_requested = users_requested.split(",")
    users_requested = [int(x) for x in users_requested] if users_requested != [''] else []
    revisions = Revision.objects.filter(valid=True).order_by("-number")
    revision = revisions.first()
    someDate = datetime.datetime.now() + datetime.timedelta(days=-61)  # default - always last two months
    scheduled_campaigns = Campaign.objects.filter(revision=revision).filter(date_end__gt=someDate)

    context = {
        'revisions': revisions,
        'displayed_revision': revision,
        'campaigns': Campaign.objects.filter(revision=revision),
        'scheduled_campaigns_list': scheduled_campaigns,
        'users': users_list,
        'users_requested': users_requested,
        'hide_studies': True,
    }
    return render(request, 'users.html', prepare_default_context(request, context))


@require_safe
def icalendar(request):
    member = None
    team = None
    if request.GET.get('mid'):
        member = Member.objects.filter(id=request.GET.get('mid')).first()
    if request.GET.get('tid'):
        team = Team.objects.filter(id=request.GET.get('tid')).first()

    revision = Revision.objects.filter(valid=True).order_by("-number").first()

    shifts = Shift.objects.filter(member=member, revision=revision)
    from .ajax import _get_companions_shift
    #  FIXME may need some optimisation in the future, it may take some time to combine all past shifts with details...
    companionShifts = _get_companions_shift(member, shifts)
    companionShiftsDates = {one.start: [one, []] for one in shifts}
    for one in companionShifts:
        companionShiftsDates[one.start][1].append(one)

    studies = StudyRequest.objects.filter(member=member, state__in=["B", "D"])
    studies_as_collaborator = StudyRequest.objects.filter(collaborators=member, state__in=["B", "D"])
    if team is not None:
        shifts = Shift.objects.filter(member__team=team, revision=revision)
        studies = StudyRequest.objects.filter(member__team=team, state__in=["B", "D"])
        studies_as_collaborator = None
    if team is None and member is None:
        shifts = Shift.objects.filter(revision=revision)
        studies = None
        studies_as_collaborator = None

    context = {
        'campaign': 'Exported Shifts',
        'shifts': shifts,
        'companionShifts': list(companionShiftsDates.values()),
        'studies': studies,
        'studies_as_collaborator': studies_as_collaborator,
        'member': member,
        'team': team if not None else member.team,
        'now': timezone.now()
    }

    body = render_to_string('icalendar.ics', context)
    return HttpResponse(body.replace('\n', '\r\n'), content_type='text/calendar')


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

    StudyFirstDay = datetime.datetime.combine(monthFirstDay, datetime.time(hour=0, minute=0, second=1, microsecond=0))
    StudyLasttDay = datetime.datetime.combine(monthLastDay, datetime.time(hour=23, minute=59, second=59, microsecond=0))
    studies = StudyRequest.objects.filter(slot_end__lte=StudyLasttDay, slot_start__gte=StudyFirstDay).filter(
        member=member, state__in=["B", "D"])

    context = {
        'campaign': 'Exported Shifts',
        'shifts': shifts,
        'studies': studies,
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
    hourToGo = request.GET.get('hour', None)
    fullUpdate = request.GET.get('fullUpdate', None) is not None
    activeShift = prepare_active_crew(dayToGo=dayToGo, slotToGo=slotToGo, hourToGo=hourToGo,
                                      fullUpdate=fullUpdate)
    dayDate = activeShift.get('today', datetime.datetime.today()).date()
    dayStudiesStart = datetime.datetime.combine(dayDate, datetime.time(hour=0, minute=0, second=1, microsecond=0))
    dayStudiesEnd = datetime.datetime.combine(dayDate, datetime.time(hour=23, minute=59, second=59, microsecond=0))
    studies = StudyRequest.objects.filter(state="B", slot_start__gte=dayStudiesStart, slot_start__lte=dayStudiesEnd). \
        order_by("slot_start")

    return JsonResponse(prepare_for_JSON(activeShift, studies=studies))


@require_safe
def shifts(request):
    shiftId = request.GET.get('id', None)
    if shiftId is not None:
        dataToReturn = {'SID': shiftId, 'status': False}
        shiftIDs = ShiftID.objects.filter(label=shiftId)
        if len(shiftIDs):
            shiftID = shiftIDs.first()
            previousShiftId = None
            try:
                previousShiftId = ShiftID.objects.get(id=shiftID.id - 1).label
            except ObjectDoesNotExist:
                pass
            nextShiftId = None
            try:
                nextShiftId = ShiftID.objects.get(id=shiftID.id + 1).label
            except ObjectDoesNotExist:
                pass
            dataToReturn = {'SID': shiftId, 'status': 'True', 'prev': previousShiftId, 'next': nextShiftId}
    else:
        shiftIds = ShiftID.objects.all().order_by('-label')
        dataToReturn = {'ids': [id.label for id in shiftIds]}
    return JsonResponse(dataToReturn)


@require_safe
def scheduled_work_time(request):
    rev = Revision.objects.filter(valid=True).order_by("-number")[0]
    startDate = None
    endDate = None
    try:
        if request.GET.get('start', None) is not None:
            startDate = datetime.datetime.strptime(request.GET.get('start'), DATE_FORMAT)
        if request.GET.get('end', None) is not None:
            endDate = datetime.datetime.strptime(request.GET.get('end'), DATE_FORMAT)
        if request.GET.get('rev', None) is not None:
            revId = int(request.GET.get('rev'))
            rev = Revision.objects.filter(valid=True).filter(number=revId)[0]
    except ValueError:
        pass
    scheduled_shifts = Shift.objects.filter(revision=rev) \
        .filter(member__role__abbreviation='SL') \
        .order_by('date', 'slot__hour_start', 'member__role__priority')
    if startDate is not None and endDate is not None:
        scheduled_shifts = scheduled_shifts.filter(date__gte=startDate) \
            .filter(date__lte=endDate)
    dataToReturn = find_working_hours(scheduled_shifts, startDate=startDate, endDate=endDate)
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
    # merge one into another
    rev1Id = request.POST.get('revision-to-move', None)
    rev2Id = request.POST.get('revision-to-merge-in', None)
    mergeFrom = request.POST.get('date-to-merge-from', None)
    # delete from one revision
    trimFrom = request.POST.get('date-to-delete-from', None)
    revToTrimId = request.POST.get('revision-to-cut', None)
    if rev2Id is not None and rev1Id is not None and mergeFrom is not None:
        d = datetime.datetime.strptime(mergeFrom, DATE_FORMAT).date()
        rev1 = Revision.objects.get(number=rev1Id)
        rev2 = Revision.objects.get(number=rev2Id)
        s1 = Shift.objects.filter(revision=rev1, date__gte=d)
        s2 = Shift.objects.filter(revision=rev2, date__gte=d)
        backupRevision = Revision.objects.filter(name__startswith='BACKUP').first()
        print(backupRevision)
        for shiftToBackup in s2:
            shiftToBackup.revision = backupRevision
            shiftToBackup.save()
        for shiftToMerge in s1:
            shiftToMerge.revision = rev2
            shiftToMerge.save()
        rev1.merged = True
        rev1.save()
        messages.success(request, 'Merged {} shifts from Revision {} in Revision: {} starting on date: {}'.
                         format(s1.count(), rev1, rev2, d))
    if revToTrimId is not None and trimFrom is not None:
        d = datetime.datetime.strptime(trimFrom, DATE_FORMAT).date()
        revToTrim = Revision.objects.get(number=revToTrimId)
        s = Shift.objects.filter(revision=revToTrim, date__gte=d)
        for shiftToDelete in s:
            shiftToDelete.delete()
        messages.success(request, 'Deleted {} shifts as from {} in Revision: {}'.
                         format(s.count(), d, revToTrim))
    return HttpResponseRedirect(reverse("desiderata.team_view",
                                        kwargs={'team_id': request.user.team.id}))


@require_safe
@login_required
def shifts_upload(request):
    data = {'campaigns': Campaign.objects.all(),
            'revisions': Revision.objects.filter(merged=False),
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
    if int(request.POST['revision']) < 1:
        revision = Revision(name=request.POST['new-revision-name'],
                            valid=False,
                            date_start=timezone.now())
        revision.save()
    else:
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
            nameFromFile = fields[0].replace(" ", "")
            for dayIndex, one in enumerate(fields):
                if dayIndex == 0:
                    continue
                one.replace(" ", "")
                slotAbbrev = one.strip()
                if slotAbbrev == '' or slotAbbrev == '-':  # neutral shift slot abbrev
                    continue
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
                    shift.save()
                    shiftRole = defaultShiftRole
                except ObjectDoesNotExist as e:
                    # print(e)
                    print("'{}' '{}' ".format(nameFromFile, slotAbbrev))
                    messages.error(request, 'Could not find system member for ({}) / slot ({}), in line {} column {}.\
                                    Skipping for now Check your file'
                                   .format(fields[0], one, lineIndex, dayIndex))

                except IntegrityError as e:
                    # print(e)
                    messages.error(request, 'Could not add member {} for {} {}, \
                                            Already in the system for the same \
                                            role: {}  campaign: {} and revision {}'
                                   .format(fields[0], shiftFullDate, one, shiftRole, campaign, revision))

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
    tmp = []
    import members.directory as directory
    ldap = directory.LDAP()
    searchKey = request.POST.get('searchKey', 'SomeNonsenseToNotBeFound')
    r = ldap.search(field='name', text=searchKey)
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
        tmp.append({'name': one,
                    'mobile': phoneNb,
                    'email': r[one]['email'],
                    'photo': photo,
                    'valid': False})

    context = {
        'result': [],
        'searchkey': searchKey
    }
    invalid = []
    for one in tmp:
        if one['mobile'] == 'N/A' or len(one['email']) == 0:
            invalid.append(one)
            continue
        one['valid'] = True
        context['result'].append(one)
    for one in invalid:
        context['result'].append(one)
    return render(request, 'phonebook.html', prepare_default_context(request, context))


class AssetsView(View):
    def get(self, request):
        form = AssetBookingForm({'member': request.user,
                                 'use_start': datetime.datetime.now().strftime(DATE_FORMAT_FULL),
                                 'use_end': datetime.datetime.now().strftime(DATE_FORMAT_FULL)},
                                user=request.user)

        closing_form = AssetBookingFormClosing()
        return render(request, 'assets.html', {'form': form, 'closing_form': closing_form})

    def post(self, request):
        form = AssetBookingForm(request.POST, user=request.user)
        if form.is_valid():
            post = form.save(commit=False)
            post.booking_created = timezone.localtime(timezone.now())
            post.booked_by = request.user
            post.save()
            message = "Booking for {} on {}, is added!".format(post.member.first_name, post.use_start)
            messages.success(request, message)
        else:
            message = "Booking form is not valid, please correct."
            messages.success(request, message)
        return redirect('assets')


@require_http_methods(["POST"])
def assets_close(request):
    booking_id = request.POST.get('booking_id')
    form = AssetBookingFormClosing(request.POST)
    if form.is_valid():
        comment = form.cleaned_data['after_comment']
        current_booking = get_object_or_404(AssetBooking, id=booking_id)
        current_booking.booking_finished = timezone.localtime(timezone.now())
        current_booking.after_comment = comment
        current_booking.state = AssetBooking.BookingState.RETURNED
        current_booking.finished_by = request.user
        current_booking.save()
        message = "Booking for {} on {}, is now closed!".format(current_booking.member.first_name,
                                                                current_booking.use_start)
        messages.success(request, message)
    else:
        message = "Booking form is not valid, please correct."
        messages.success(request, message)
    return redirect('assets')
