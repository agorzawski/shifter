from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, HttpResponse, HttpRequest
from django.shortcuts import render

from django.views.decorators.http import require_safe

import datetime
from shifts.models import Desiderata, Revision
from members.models import Team
from django.utils.timezone import make_aware
from django.utils import timezone
import json
from django.db.models import Q
from django.shortcuts import get_object_or_404
from guardian.shortcuts import get_objects_for_user


@require_safe
@login_required
def team_view(request: HttpRequest, team_id: int) -> HttpResponse:
    today = datetime.datetime.now()
    year = today.year
    month = today.month

    default_start = datetime.date(year, month, 1)
    default_end = datetime.date(year, month + 1, 1) + datetime.timedelta(days=-1)

    the_team = get_object_or_404(Team, id=team_id)
    logged_user = request.user
    logged_user_manage = get_objects_for_user(logged_user, 'members.view_desiderata')
    if the_team not in logged_user_manage:
        raise PermissionDenied
    # Here we are sure the team exists, and the user has the right to see the full desiderata
    return render(request, 'team_desiderata.html', {'team': the_team,
                                                    'default_start': default_start,
                                                    'default_end': default_end,
                                                    'latest_revision': Revision.objects.filter(valid=True).order_by('-number').first(),
                                                    'revisions': Revision.objects.order_by('-number')}
                                                    )


@require_safe
@login_required
def user(request: HttpRequest) -> HttpResponse:
    member = request.user
    desiderata_types = Desiderata.DesiderataType
    return render(request, 'user_desiderata.html', {'member': member, 'desiderata_types': desiderata_types})


@require_safe
@login_required
def add(request: HttpRequest) -> HttpResponse:
    the_user = request.user
    all_day = True if request.GET.get('allDay', 'false') == 'true' else False
    date_start = datetime.datetime.fromisoformat(request.GET.get('startStr'))
    date_end = datetime.datetime.fromisoformat(request.GET.get('endStr'))
    event_type = request.GET.get('event_type')
    assert event_type in Desiderata.DesiderataType
    date_start = make_aware(date_start, timezone.get_current_timezone())
    date_end = make_aware(date_end, timezone.get_current_timezone())
    the_desiderata = Desiderata(start=date_start,
                                stop=date_end,
                                member=the_user,
                                all_day=all_day,
                                type=event_type,
                                )
    the_desiderata.save()
    return JsonResponse({}, status=200)


@require_safe
@login_required
def edit(request: HttpRequest) -> HttpResponse:
    the_user = request.user
    all_day = True if request.GET.get('allDay', 'false') == 'true' else False
    date_start = datetime.datetime.fromisoformat(request.GET.get('startStr'))
    string_end = request.GET.get('endStr')
    if string_end == "":
        date_start = datetime.datetime(year=date_start.year,
                                       month=date_start.month,
                                       day=date_start.day,
                                       hour=10,
                                       minute=0)
        date_end = date_start + datetime.timedelta(hours=2)
    else:
        date_end = datetime.datetime.fromisoformat(string_end)

    event_id = int(request.GET.get('id'))

    the_event = Desiderata.objects.get(id=event_id, member=the_user)

    the_event.all_day = all_day
    the_event.start = make_aware(date_start, timezone.get_current_timezone())
    the_event.stop = make_aware(date_end, timezone.get_current_timezone())
    
    the_event.save()
    return JsonResponse({}, status=200)


def delete(request: HttpRequest) -> HttpResponse:
    the_user = request.user
    event_id = int(request.GET.get('id'))

    the_event = Desiderata.objects.get(id=event_id, member=the_user)

    the_event.delete()
    return JsonResponse({}, status=200)


@require_safe
@login_required
def get_team_desiderata(request: HttpRequest) -> HttpResponse:
    the_team = get_object_or_404(Team, id=request.GET.get('team'))
    logged_user = request.user
    logged_user_manage = get_objects_for_user(logged_user, 'members.view_desiderata')
    if the_team not in logged_user_manage:
        raise PermissionDenied
    # Here we are sure the team exists, and the user has the right to see the full desiderata
    calendar_events = get_desiderata_in_date_range_from_request(request, for_team=the_team)
    return HttpResponse(json.dumps(calendar_events), content_type="application/json")


@require_safe
@login_required
def get_team_desiderata_non_rota_maker(request: HttpRequest) -> HttpResponse:
    the_team = get_object_or_404(Team, id=request.user.team.id)
    to_show = request.GET.get('show', False)
    if to_show == 'false':
        return HttpResponse(json.dumps([]), content_type="application/json")
    logged_user = request.user
    if the_team != logged_user.team:
        raise PermissionDenied
    # Here we are sure the team exists, and the user has the right to see the full desiderata
    calendar_events = get_desiderata_in_date_range_from_request(request, for_team=the_team, editable=False, exclude=request.user)
    return HttpResponse(json.dumps(calendar_events), content_type="application/json")


@require_safe
@login_required
def get_user_desiderata(request: HttpRequest) -> HttpResponse:
    calendar_events = get_desiderata_in_date_range_from_request(request)
    return HttpResponse(json.dumps(calendar_events), content_type="application/json")


def get_desiderata_in_date_range_from_request(request, for_team=None, editable=True, exclude=False):
    start_date = request.GET.get('start', None)
    end_date = request.GET.get('end', None)

    if start_date is None or end_date is None:
        return HttpResponse({}, content_type="application/json", status=500)

    start = datetime.datetime.fromisoformat(start_date)
    end = datetime.datetime.fromisoformat(end_date)

    start = make_aware(start, timezone.get_current_timezone())
    end = make_aware(end, timezone.get_current_timezone())

    criterion1 = Q(start__lte=start)
    criterion2 = Q(stop__gte=start)

    criterion3 = Q(start__gte=start)
    criterion4 = Q(stop__lte=end)

    criterion5 = Q(start__lte=end)
    criterion6 = Q(stop__gte=end)

    the_date_filter = criterion1 & criterion2 | criterion3 & criterion4 | criterion5 & criterion6

    if for_team:
        if not exclude:
            the_calendar = Desiderata.objects.filter(member__team__id=for_team.id).filter(the_date_filter)
        else:
            the_calendar = Desiderata.objects.filter(member__team__id=for_team.id).filter(the_date_filter).exclude(member=exclude)
    else:
        member = request.user
        the_calendar = Desiderata.objects.filter(member=member).filter(the_date_filter)

    calendar_events = [d.get_as_json_event(team=True if for_team else False, editable=editable) for d in the_calendar]

    return calendar_events
