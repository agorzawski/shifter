from django.http import HttpResponse, JsonResponse
from django.http import HttpRequest
from django.views.decorators.http import require_safe
from shifts.models import *
import datetime
from members.models import Team
from .hrcodes import public_holidays, public_holidays_special
from shifts.models import SIMPLE_DATE
import json


@require_safe
def get_revision_name(request: HttpRequest) -> JsonResponse:
    revision = request.GET.get('revision', None)
    revision = Revision.objects.get(valid=True, number=revision)
    return JsonResponse({'name': str(revision)})


@require_safe
def get_user_events(request: HttpRequest) -> HttpResponse:
    start_date = request.GET.get('start', None)
    end_date = request.GET.get('end', None)

    if start_date is None or end_date is None:
        return HttpResponse({}, content_type="application/json", status=500)

    start = datetime.datetime.fromisoformat(start_date).date() - datetime.timedelta(days=1)
    end = datetime.datetime.fromisoformat(end_date).date() + datetime.timedelta(days=1)

    member_id = request.GET.get('member', -1)
    if member_id == -1:
        member = request.user
    else:
        member = Member.objects.filter(id=member_id).first()

    scheduled_shifts = Shift.objects.filter(revision=Revision.objects.filter(valid=True).order_by('-number').first())\
        .filter(member=member).filter(date__gt=start).filter(date__lt=end)

    calendar_events = [d.get_shift_as_json_event() for d in scheduled_shifts]
    return HttpResponse(json.dumps(calendar_events), content_type="application/json")


@require_safe
def get_team_events(request: HttpRequest) -> HttpResponse:
    start_date = request.GET.get('start', None)
    end_date = request.GET.get('end', None)

    if start_date is None or end_date is None :
        return HttpResponse({}, content_type="application/json", status=500)

    start = datetime.datetime.fromisoformat(start_date).date() - datetime.timedelta(days=1)
    end = datetime.datetime.fromisoformat(end_date).date() + datetime.timedelta(days=1)

    team_id = request.GET.get('team', -1)
    if team_id == -1:
        team = request.user.team
    else:
        team = Team.objects.filter(id=int(team_id)).first()
    revision = Revision.objects.filter(valid=True).order_by("-number").first()
    scheduled_shifts = Shift.objects.filter(member__team=team, revision=revision)\
        .filter(date__gt=start).filter(date__lt=end)
    calendar_events = [d.get_shift_as_json_event() for d in scheduled_shifts]
    return HttpResponse(json.dumps(calendar_events), content_type="application/json")


@require_safe
def get_events(request: HttpRequest) -> HttpResponse:
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

    scheduled_shifts = Shift.objects.filter(revision=revision).filter(campaign__in=scheduled_campaigns)\
                            .filter(role=None) \
                            .filter(date__gt=start) \
                            .filter(date__lt=end) \
        .order_by('date', 'slot__hour_start', 'member__role__priority')
    if all_roles:
        scheduled_shifts = Shift.objects.filter(revision=revision).filter(campaign__in=scheduled_campaigns) \
            .filter(date__gt=start) \
            .filter(date__lt=end) \
            .order_by('date', 'slot__hour_start', 'member__role__priority')

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
                        'overlap': False,
                        'display': 'background'} for d in ph]
    return HttpResponse(json.dumps(calendar_events), content_type="application/json")
