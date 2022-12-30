from django.http import HttpResponse, JsonResponse
from django.http import HttpRequest
from django.views.decorators.http import require_safe
from shifts.models import *
import datetime
from members.models import Team
from assets.models import AssetBooking
from shifts.hrcodes import public_holidays, public_holidays_special
from shifts.models import SIMPLE_DATE
import json


@require_safe
def get_revision_name(request: HttpRequest) -> JsonResponse:
    revision = request.GET.get('revision', None)
    revision = Revision.objects.get(valid=True, number=revision)
    return JsonResponse({'name': str(revision)})


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
    return Shift.objects.filter(revision=Revision.objects.filter(valid=True).order_by('-number').first())\
        .filter(member=_get_member(request)).filter(date__gt=start).filter(date__lt=end)


@require_safe
def get_user_events(request: HttpRequest) -> HttpResponse:
    calendar_events = [d.get_shift_as_json_event() for d in _get_scheduled_shifts(request)]
    return HttpResponse(json.dumps(calendar_events), content_type="application/json")


@require_safe
def get_user_future_events(request: HttpRequest) -> HttpResponse:
    calendar_events = [d.get_shift_as_json_event() for d in _get_scheduled_shifts(request)]
    revisionNext = request.GET.get('revision_next', -1)
    if revisionNext != -1:
        revisionNext = Revision.objects.get(number=revisionNext)
        future_scheduled_shifts = Shift.objects.filter(member=_get_member(request),
                                                       revision=revisionNext)
        for d in future_scheduled_shifts:
            calendar_events.append(d.get_planned_shift_as_json_event())
    return HttpResponse(json.dumps(calendar_events), content_type="application/json")


# @require_safe
# def get_team_events(request: HttpRequest) -> HttpResponse:
#     start_date = request.GET.get('start', None)
#     end_date = request.GET.get('end', None)
#
#     if start_date is None or end_date is None :
#         return HttpResponse({}, content_type="application/json", status=500)
#
#     start = datetime.datetime.fromisoformat(start_date).date() - datetime.timedelta(days=1)
#     end = datetime.datetime.fromisoformat(end_date).date() + datetime.timedelta(days=1)
#
#     team_id = request.GET.get('team', -1)
#     if team_id == -1:
#         team = request.user.team
#     else:
#         team = Team.objects.filter(id=int(team_id)).first()
#     revision = Revision.objects.filter(valid=True).order_by("-number").first()
#     scheduled_shifts = Shift.objects.filter(member__team=team, revision=revision)\
#         .filter(date__gt=start).filter(date__lt=end)
#     calendar_events = [d.get_shift_as_json_event() for d in scheduled_shifts]
#     return HttpResponse(json.dumps(calendar_events), content_type="application/json")


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
    if not all_roles:
        filter_dic['role'] = None
    if int(team_id) > 0:
        team = Team.objects.get(id=team_id)
        filter_dic['member__team'] = team
    scheduled_shifts = Shift.objects.filter(**filter_dic).order_by('date', 'slot__hour_start', 'member__role__priority')

    #
    #
    #
    #
    # scheduled_shifts = Shift.objects.filter(revision=revision).filter(campaign__in=scheduled_campaigns)\
    #                         .filter(role=None) \
    #                         .filter(date__gt=start) \
    #                         .filter(date__lt=end) \
    #     .order_by('date', 'slot__hour_start', 'member__role__priority')
    # if all_roles:
    #     scheduled_shifts = Shift.objects.filter(revision=revision).filter(campaign__in=scheduled_campaigns) \
    #         .filter(date__gt=start) \
    #         .filter(date__lt=end) \
    #         .order_by('date', 'slot__hour_start', 'member__role__priority')

    calendar_events = [d.get_shift_as_json_event() for d in scheduled_shifts]

    return HttpResponse(json.dumps(calendar_events), content_type="application/json")


@require_safe
def get_holidays(request: HttpRequest) -> HttpResponse:
    start = datetime.datetime.fromisoformat(request.GET.get('start')).date()
    end = datetime.datetime.fromisoformat(request.GET.get('end')).date()

    ph = [x for x in public_holidays_special + public_holidays if start <= x <= end]
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
