from django.http import HttpResponse, JsonResponse
from django.http import HttpRequest
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_safe
from shifts.models import *
from studies.models import *
import datetime
from members.models import Team
from assets.models import AssetBooking
from shifts.hrcodes import red_days, public_holidays_special
from shifts.models import SIMPLE_DATE
from shifts.hrcodes import get_public_holidays, get_date_code_counts, count_total
from shifter.settings import DEFAULT_SPECIAL_SHIFT_ROLES
from shifts.workinghours import find_daily_rest_time_violation, find_weekly_rest_time_violation, get_hours_break
import json
from watson import search as watson
from guardian.shortcuts import get_objects_for_user
from django.core.exceptions import PermissionDenied


def _get_member(request: HttpRequest):
    member_id = request.GET.get('member', -1)
    if member_id == -1:
        member = request.user
    else:
        member = Member.objects.filter(id=member_id).first()
    return member


def _get_revision(request: HttpRequest):
    revision = int(request.GET.get('revision', -1))
    if revision == -1:
        revision = Revision.objects.filter(valid=True).order_by("-number").first()
    else:
        revision = Revision.objects.get(number=revision)
    return revision


def _get_scheduled_shifts(request: HttpRequest):
    start_date = request.GET.get('start', None)
    end_date = request.GET.get('end', None)
    if start_date is None or end_date is None:
        return HttpResponse({}, content_type="application/json", status=500)
    start = datetime.datetime.fromisoformat(start_date).date() - datetime.timedelta(days=1)
    end = datetime.datetime.fromisoformat(end_date).date() + datetime.timedelta(days=1)
    filter_dic = {'revision': Revision.objects.filter(valid=True).order_by('-number').first(),
                  'date__lte': end, 'date__gte':start, 'member': _get_member(request),
                  'is_cancelled': False, 'is_active': True}
    return Shift.objects.filter(**filter_dic)


def _get_companions_shift(member: Member, base_scheduled_shifts):
    filteredCompanions = []
    filter_dic = {'date__in': [s.date for s in base_scheduled_shifts],
                  'revision__in': [s.revision for s in base_scheduled_shifts],
                  'role': None,
                  'is_cancelled': False,
                  'is_active': True}
    future_companion_shifts = Shift.objects.filter(**filter_dic) \
        .filter(~Q(member=member))
    future_companion_exact_shifts = [d.start for d in base_scheduled_shifts]
    for d in future_companion_shifts:
        if d.start in future_companion_exact_shifts:
            filteredCompanions.append(d)
    return filteredCompanions


@require_safe
def get_user_events(request: HttpRequest) -> HttpResponse:
    base_scheduled_shifts = _get_scheduled_shifts(request)
    calendar_events = [d.get_shift_as_json_event() for d in base_scheduled_shifts]
    revisionNext = request.GET.get("revision_next", default='-1')
    revisionNext = int(revisionNext)
    if revisionNext != -1:
        revisionNext = Revision.objects.get(number=revisionNext)
        future_scheduled_shifts = Shift.objects.filter(member=_get_member(request),
                                                       revision=revisionNext)
        for d in future_scheduled_shifts:
            calendar_events.append(d.get_planned_shift_as_json_event())
    withCompanion = request.GET.get("companion", default=None)
    withCompanion = True if withCompanion == "true" else False
    if withCompanion:
        for d in _get_companions_shift(_get_member(request), base_scheduled_shifts):
            calendar_events.append(d.get_shift_as_json_event())
    return HttpResponse(json.dumps(calendar_events), content_type="application/json")


@require_safe
def get_users_events(request: HttpRequest) -> HttpResponse:
    users_requested = request.GET.get('users', '')
    users_requested = users_requested.split(",")
    users_requested = [int(x) for x in users_requested] if users_requested != [''] else []

    start_date = request.GET.get('start', None)
    end_date = request.GET.get('end', None)
    all_roles = request.GET.get('all_roles', None)
    campaigns = request.GET.get('campaigns', None)
    revision = _get_revision(request)

    if start_date is None or end_date is None or all_roles is None or campaigns is None or revision is None:
        return HttpResponse({}, content_type="application/json", status=500)

    campaigns = campaigns.split(",")
    campaigns = [int(x) for x in campaigns] if campaigns != [''] else []
    all_roles = True if all_roles == "true" else False
    start = datetime.datetime.fromisoformat(start_date).date() - datetime.timedelta(days=1)
    end = datetime.datetime.fromisoformat(end_date).date() + datetime.timedelta(days=1)
    scheduled_campaigns = Campaign.objects.filter(revision=revision).filter(id__in=campaigns)

    filter_dic = {'date__gt': start, 'date__lt': end, 'revision': revision, 'campaign__in': scheduled_campaigns,
                  'member_id__in': users_requested,
                  'is_cancelled': False, 'is_active': True}

    scheduled_shifts = Shift.objects.filter(**filter_dic).order_by('date', 'slot__hour_start', 'member__role__priority')
    if not all_roles:
        scheduled_shifts = scheduled_shifts.filter(Q(role=None) |
                                                   Q(role__in=[one for one in ShiftRole.objects.filter(
                                                       abbreviation__in=DEFAULT_SPECIAL_SHIFT_ROLES)]))
    calendar_events = [d.get_shift_as_json_event() for d in scheduled_shifts]
    return HttpResponse(json.dumps(calendar_events), content_type="application/json")


@require_safe
def get_events(request: HttpRequest) -> HttpResponse:
    start_date = request.GET.get('start', None)
    end_date = request.GET.get('end', None)
    all_roles = request.GET.get('all_roles', None)
    campaigns = request.GET.get('campaigns', None)
    revision = request.GET.get('revision', None)
    team_id = request.GET.get('team', -1)

    if start_date is None or end_date is None or all_roles is None or campaigns is None or revision is None:
        return HttpResponse({}, content_type="application/json", status=500)

    campaigns = campaigns.split(",")
    campaigns = [int(x) for x in campaigns] if campaigns != [''] else []
    all_roles = True if all_roles == "true" else False
    start = datetime.datetime.fromisoformat(start_date).date() - datetime.timedelta(days=1)
    end = datetime.datetime.fromisoformat(end_date).date() + datetime.timedelta(days=1)
    revision = int(revision)

    if revision == -1:
        revision = Revision.objects.filter(valid=True).order_by("-number").first()
    else:
        revision = Revision.objects.get(valid=True, number=revision)
    scheduled_campaigns = Campaign.objects.filter(revision=revision).filter(id__in=campaigns)

    filter_dic = {'date__gt': start, 'date__lt': end, 'revision': revision, 'campaign__in': scheduled_campaigns,
                  'is_cancelled': False, 'is_active': True}
    if int(team_id) > 0:
        team = Team.objects.get(id=team_id)
        filter_dic['member__team'] = team
    scheduled_shifts = Shift.objects.filter(**filter_dic).order_by('date', 'slot__hour_start', 'member__role__priority')
    if not all_roles:
        scheduled_shifts = scheduled_shifts.filter(Q(role=None) |
                                                   Q(role__in=[one for one in ShiftRole.objects.filter(
                                                       abbreviation__in=DEFAULT_SPECIAL_SHIFT_ROLES)]))

    calendar_events = [d.get_shift_as_json_event() for d in scheduled_shifts]

    return HttpResponse(json.dumps(calendar_events), content_type="application/json")


@require_safe
def get_holidays(request: HttpRequest) -> HttpResponse:
    start = datetime.datetime.fromisoformat(request.GET.get('start')).date()
    end = datetime.datetime.fromisoformat(request.GET.get('end')).date()

    ph = [x for x in public_holidays_special + red_days if start <= x <= end]
    ph.sort()

    calendar_events = [{'start': d.strftime(format=SIMPLE_DATE),
                        'end': d.strftime(format=SIMPLE_DATE),
                        'overlap': True,
                        'color': "#8fdf82",
                        'display': 'background'} for d in ph]
    return HttpResponse(json.dumps(calendar_events), content_type="application/json")


@require_safe
def get_assets(request: HttpRequest) -> HttpResponse:
    bookings = AssetBooking.objects.all().order_by('-use_start')
    data = {"data": [b.asset_as_json(user=request.user) for b in bookings]}
    return JsonResponse(data)


@require_safe
@login_required()
def get_hr_codes(request: HttpRequest) -> HttpResponse:
    member = request.user

    default_start = datetime.datetime.strptime(request.GET.get('start', '2022/01/01'), '%Y-%m-%d').date()
    default_end = datetime.datetime.strptime(request.GET.get('end', '2022/01/01'), '%Y-%m-%d').date()

    revision = Revision.objects.filter(valid=True).order_by("-number").first()

    filter_dic = {'date__gte': default_start, 'date__lte': default_end, 'revision': revision, 'member': member,
                  'is_active': True}

    scheduled_shifts = Shift.objects.filter(**filter_dic).order_by("-date")

    shift2codes = get_date_code_counts(scheduled_shifts)

    data = []
    for date, item in shift2codes.items():
        a_row = [date, item['OB1'], item['OB2'], item['OB3'], item['OB4'], item['NWH']]
        data.append(a_row)

    return HttpResponse(json.dumps({'data': data}), content_type="application/json")


@require_safe
@login_required()
def get_team_hr_codes(request: HttpRequest) -> HttpResponse:
    logged_user = request.user
    logged_user_manage = get_objects_for_user(logged_user, 'members.view_desiderata')

    default_start = datetime.datetime.strptime(request.GET.get('start', '2022/01/01'), '%Y-%m-%d').date()
    default_end = datetime.datetime.strptime(request.GET.get('end', '2022/01/01'), '%Y-%m-%d').date()
    team = request.GET.get('team', -1)
    team = Team.objects.get(id=team)
    if team not in logged_user_manage:
        raise PermissionDenied
    team_members = Member.objects.filter(team=team).filter(is_active=True)

    revision = Revision.objects.filter(valid=True).order_by("-number").first()
    data = []

    for m in team_members:
        filter_dic = {'date__gte': default_start, 'date__lte': default_end, 'revision': revision, 'member': m,
                      'is_active': True}

        scheduled_shifts = Shift.objects.filter(**filter_dic).order_by("-date")

        shift2codes = get_date_code_counts(scheduled_shifts)

        for date, item in shift2codes.items():
            a_row = [date, str(m), item['OB1'], item['OB2'], item['OB3'], item['OB4'], item['NWH']]
            data.append(a_row)

    return HttpResponse(json.dumps({'data': data}), content_type="application/json")


def get_shift_summary(m, validSlots, revision, start, end) -> tuple:
    scheduled_shifts = Shift.objects.filter(member=m,
                                            slot__in=validSlots,
                                            revision=revision,
                                            date__gte=start,
                                            date__lt=end).count()

    differentSlots = Shift.objects.filter(member=m,
                                          slot__in=validSlots,
                                          revision=revision,
                                          date__gte=start,
                                          date__lt=end) \
        .values('slot__abbreviation') \
        .annotate(total=Count('slot'))

    result = {a['slot__abbreviation']: a['total'] for a in differentSlots}
    return scheduled_shifts, result


@login_required
def get_shift_breakdown(request: HttpRequest) -> HttpResponse:
    start = datetime.datetime.fromisoformat(request.GET.get('start')).date()
    end = datetime.datetime.fromisoformat(request.GET.get('end')).date()
    revision = _get_revision(request)
    team = request.user.team

    teamMembers = Member.objects.filter(team=team, is_active=True)
    validSlots = Slot.objects.filter(used_for_lookup=True).order_by('hour_start')
    teamMembersSummary = []
    for m in teamMembers:
        l, result = get_shift_summary(m, validSlots, revision, start, end)
        memberSummary = [m.name, l]
        for oneSlot in validSlots:
            memberSummary.append(result.get(oneSlot.abbreviation, '--'))
        if memberSummary[1] > 0:
            teamMembersSummary.append(memberSummary)

    header = f'Showing shift breakdown from {start.strftime("%A, %B %d, %Y ")} to {(end - datetime.timedelta(days=1)).strftime("%A, %B %d, %Y ")}'

    return HttpResponse(json.dumps({'data': teamMembersSummary,
                                    'header': header,
                                    'date-start': start.strftime(DATE_FORMAT_FULL),
                                    'date-end': end.strftime(DATE_FORMAT_FULL),
                                    'slots': [one.__str__() for one in validSlots],
                                    'userdata': [{} for one in teamMembersSummary],
                                    'revision': revision.__str__()}), content_type="application/json")


@login_required
def get_shifts_for_exchange(request: HttpRequest) -> HttpResponse:
    member = _get_member(request)
    revision = _get_revision(request)
    toReturn = []
    if request.GET.get('option', 'my') == 'my':
        futureMy = Shift.objects.filter(revision=revision, member=member, date__gte=timezone.now()).order_by("date")
        toReturn = [s.get_simplified_as_json() for s in futureMy]
    if request.GET.get('option', 'my') == 'them':
        futureOther = Shift.objects.filter(~Q(member=member),revision=revision,
                                           date__gte=timezone.now()).order_by("date")
        toReturn = [s.get_simplified_as_json() for s in futureOther]
    return HttpResponse(json.dumps(toReturn), content_type="application/json")


def _get_inconsistencies_per_member(member, revision):
    # TODO fix it with proper js file to build it out of JSON
    # TODO once with json, return count of inconsistencies to enable badge
    ss = Shift.objects.filter(revision=revision).filter(member=member)
    dailyViolations = find_daily_rest_time_violation(scheduled_shifts=ss)
    weeklyViolations = find_weekly_rest_time_violation(scheduled_shifts=ss)
    toReturnHTML = ""
    if len(dailyViolations):
        toReturnHTML += "<dl class=\"row\">" \
                                "<dt class=\"col-sm-3\">Daily shift issues:</dt>" \
                                "<dd class=\"col-sm-9\">"
        for oneD in dailyViolations:
            label = 'light'
            if oneD[0].start > datetime.datetime.now():
                label = 'danger'
            toReturnHTML += f"<p><span class=\"badge text-bg-{label}\">{oneD[0].get_shift_as_date_slot()}</span> - " \
                            f"<span class=\"badge text-bg-{label}\">{oneD[1].get_shift_as_date_slot()} </span> " \
                            f"<span class=\"badge text-bg-dark\">{get_hours_break(oneD[1], oneD[0])}h</span></p>"
        toReturnHTML += "</dd></dl>"
    if len(weeklyViolations):
        toReturnHTML += "<dl class=\"row\">" \
                        "<dt class=\"col-sm-3\">Weekly shift issues:</dt>" \
                        "<dd class=\"col-sm-9\">"
        for oneW in weeklyViolations:
            for i, oneInW in enumerate(oneW):
                label = 'light'
                if oneInW.start > datetime.datetime.now():
                    label = 'danger'
                breakLength = ""
                if i < len(oneW)-1:
                    breakLength = f"<span class=\"badge text-bg-dark\">{get_hours_break(oneW[i + 1], oneInW)}h</span>"
                toReturnHTML += f"<p><span class=\"badge text-bg-{label}\">{oneInW.get_shift_as_date_slot()}</span>{breakLength}</p>"
            toReturnHTML += "<hr>"
        toReturnHTML += "</dd></dl>"
    if len(dailyViolations) or len(weeklyViolations):
        return toReturnHTML
    else:
        return None


@login_required
def get_shift_inconsistencies(request: HttpRequest) -> HttpResponse:
    revision = _get_revision(request)
    toReturnHTML = _get_inconsistencies_per_member(request.user, revision)
    return HttpResponse(toReturnHTML, content_type="application/text")


@login_required
def get_team_shift_inconsistencies(request: HttpRequest) -> HttpResponse:
    revision = _get_revision(request)
    team = request.user.team
    teamId = int(request.GET.get('tid', -1))
    if teamId > 0:
        team = Team.objects.get(id=teamId)
    members = Member.objects.filter(team=team, is_active=True)
    # TODO improve when _get_per_member's TODOs solved
    toReturnHTML = ""
    for member in members:
        foundInconsistencies = _get_inconsistencies_per_member(member, revision)
        if foundInconsistencies is not None:
            toReturnHTML += "<hr><h5 class=\"mb-3\">{}</h5>".format(member)
            toReturnHTML += foundInconsistencies
    return HttpResponse(toReturnHTML, content_type="application/text")


@login_required
def get_shift_stats(request: HttpRequest) -> HttpResponse:
    start_date = request.GET.get('start', None)
    end_date = request.GET.get('end', None)
    statType = request.GET.get('statType', None)
    teamId = request.GET.get('teamId', -1)
    teamId = int(teamId)
    revision = _get_revision(request)
    start = datetime.datetime.fromisoformat(start_date).date()
    end = datetime.datetime.fromisoformat(end_date).date()
    shifts4Stat = Shift.objects.filter(revision=revision)\
                               .filter(member__team__id=teamId)\
                               .filter(date__gte=start).filter(date__lte=end).order_by('date')
    dataToReturn = []
    if statType == 'workWith':
        # FIXME there is no way to have distinct in sqllite hence the next few lines
        differentMembers = []
        differentShiftStarts = []
        for s in shifts4Stat:
            differentShiftStarts.append(s.start)
            differentMembers.append(s.member)
        differentMembers = list(set(differentMembers))
        differentShiftStarts = list(set(differentShiftStarts))
        differentShiftStarts.sort()
        # prepare the counter
        dataCount ={}
        for dm in differentMembers:
            dataCount[dm] = {}
            for dmX in differentMembers:
                if dmX == dm:
                    continue
                dataCount[dm][dmX] = 0
        # count
        for oneShiftStart in differentShiftStarts:
            temp = []
            # find same shifts (date + slot)
            for oneShift in shifts4Stat:
                if oneShift.start == oneShiftStart:
                    temp.append(oneShift)
            # count the encounters
            for one in temp:
                for second in temp:
                    if one.member == second.member:
                        continue
                    dataCount[one.member][second.member] += 1
        dataToReturn = []
        for one in dataCount.keys():
            for second in dataCount[one]:
                if dataCount[one][second] != 0:
                    dataToReturn.append([one.first_name, second.first_name, dataCount[one][second]])
    header = f'Showing shift companions from {start.strftime("%A, %B %d, %Y ")} to {(end - datetime.timedelta(days=1)).strftime("%A, %B %d, %Y ")}'
    return HttpResponse(json.dumps({'data': dataToReturn,
                                    'header': header,
                                    'date-start': start.strftime(DATE_FORMAT_FULL),
                                    'date-end': end.strftime(DATE_FORMAT_FULL),
                                    'revision': revision.__str__()}), content_type="application/json")


def search(request: HttpRequest) -> HttpResponse:
    answer = []
    search = request.GET.get('search')
    search_results = watson.search(search, ranking=False)
    for result in search_results:
        try:
            answer.append({'value': result.object.search_display(), 'url': result.object.search_url()})
        except AttributeError:
            pass
    return HttpResponse(json.dumps(answer), content_type="application/json")
