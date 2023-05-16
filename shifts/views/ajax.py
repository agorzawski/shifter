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


def _get_scheduled_shifts(request: HttpRequest):
    start_date = request.GET.get('start', None)
    end_date = request.GET.get('end', None)
    if start_date is None or end_date is None:
        return HttpResponse({}, content_type="application/json", status=500)
    start = datetime.datetime.fromisoformat(start_date).date() - datetime.timedelta(days=1)
    end = datetime.datetime.fromisoformat(end_date).date() + datetime.timedelta(days=1)
    return Shift.objects.filter(revision=Revision.objects.filter(valid=True).order_by('-number').first()) \
        .filter(member=_get_member(request)).filter(date__gte=start).filter(date__lte=end)


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
        future_companion_shifts = Shift.objects.filter(date__in=[s.date for s in base_scheduled_shifts]) \
                                               .filter(revision__in=[s.revision for s in base_scheduled_shifts])\
                                               .filter(~Q(member=_get_member(request)))
        future_companion_exact_shifts = [d.start for d in base_scheduled_shifts]
        for d in future_companion_shifts:
            if d.start in future_companion_exact_shifts:
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
    revision = request.GET.get('revision', None)

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
                  'member_id__in': users_requested}

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

    filter_dic = {'date__gt': start, 'date__lt': end, 'revision': revision, 'campaign__in': scheduled_campaigns}
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

    filter_dic = {'date__gte': default_start, 'date__lte': default_end, 'revision': revision, 'member': member}

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
        filter_dic = {'date__gte': default_start, 'date__lte': default_end, 'revision': revision, 'member': m}

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
    revision = Revision.objects.filter(valid=True).order_by("-number").first()
    team = request.user.team

    teamMembers = Member.objects.filter(team=team, is_active=True)
    validSlots = Slot.objects.filter(used_for_lookup=True).order_by('hour_start')
    teamMembersSummary = []
    for m in teamMembers:
        l, result = get_shift_summary(m, validSlots, revision, start, end)
        memberSummary = [m.name, l]
        for oneSlot in validSlots:
            memberSummary.append(result.get(oneSlot.abbreviation, '--'))
        teamMembersSummary.append(memberSummary)

    header = f'Showing shift breakdown from {start.strftime("%A, %B %d, %Y ")} to {(end - datetime.timedelta(days=1)).strftime("%A, %B %d, %Y ")}'

    return HttpResponse(json.dumps({'data': teamMembersSummary, 'header': header}), content_type="application/json")


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
