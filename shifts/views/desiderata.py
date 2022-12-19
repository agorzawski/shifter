from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse, HttpRequest
from django.shortcuts import render

from django.template.loader import render_to_string
from django.urls import reverse
import django.contrib.messages as messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods, require_safe
from django.db import IntegrityError

import members.models
from members.models import Team
from shifts.models import *
from assets.models import *
from assets.forms import AssetBookingForm, AssetBookingFormClosing
import datetime
import phonenumbers
from shifts.activeshift import prepare_active_crew, prepare_for_JSON
from shifts.contexts import prepare_default_context, prepare_user_context, prepare_team_context
from shifter.settings import DEFAULT_SHIFT_SLOT
from shifts.workinghours import find_daily_rest_time_violation, find_weekly_rest_time_violation
import datetime
from shifts.models import Desiderata
from django.utils.timezone import make_aware
from django.conf import settings
from django.utils import timezone
import json
from django.db.models import Q
from django.shortcuts import get_object_or_404
from guardian.shortcuts import get_objects_for_user


@require_safe
@login_required
def team_view(request: HttpRequest, team_id: int) -> HttpResponse:
    the_team = get_object_or_404(Team, id=team_id)
    logged_user = request.user
    logged_user_manage = get_objects_for_user(logged_user, 'members.view_desiderata')
    if the_team not in logged_user_manage:
        raise PermissionDenied
    # Here we are sure the team exists, and the user has the right to see the full desiderata
    context = {'browsable': True}
    return render(request, 'team_desiderata.html',
                  prepare_default_context(request,
                                          prepare_team_context(request,
                                                               member=logged_user,
                                                               team=the_team,
                                                               extraContext=context)))


@require_safe
@login_required
def user(request: HttpRequest) -> HttpResponse:
    member = request.user
    desiderata_types = Desiderata.DesiderataType
    context = {'browsable': True,
               'desiderata_types': desiderata_types}
    return render(request, 'user_desiderata.html',
                  prepare_default_context(request,
                                          prepare_team_context(request,
                                                               member=member,
                                                               team=None,
                                                               extraContext=context)))


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
def get_user_desiderata(request: HttpRequest) -> HttpResponse:
    calendar_events = get_desiderata_in_date_range_from_request(request)
    return HttpResponse(json.dumps(calendar_events), content_type="application/json")


def get_desiderata_in_date_range_from_request(request, for_team=None):
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
        the_calendar = Desiderata.objects.filter(member__team__id=for_team.id).filter(the_date_filter)
    else:
        member = request.user
        the_calendar = Desiderata.objects.filter(member=member).filter(the_date_filter)

    calendar_events = [d.get_as_json_event(team=True if for_team else False) for d in the_calendar]

    return calendar_events
