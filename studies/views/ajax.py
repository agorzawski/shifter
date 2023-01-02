from django.http import HttpResponse, JsonResponse
from django.http import HttpRequest
from studies.models import *
import json

def _get_member(request: HttpRequest):
    member_id = request.GET.get('member', -1)
    if member_id == -1:
        member = request.user
    else:
        member = Member.objects.filter(id=member_id).first()
    return member


def get_studies(request: HttpRequest) -> HttpResponse:
    team_id = int(request.GET.get('team', -1))
    member_id = int(request.GET.get('member', -1))
    show_studies = request.GET.get('show_studies', False)
    show_studies = True if show_studies == "true" else False

    studies_events = []
    if team_id < 0 and member_id < 0:
        if show_studies:
            scheduled_studies = StudyRequest.objects.filter(
                                                            state__in=["B", "D"]).order_by('slot_start', 'priority')
            studies_events = [d.get_study_as_json_event() for d in scheduled_studies]
    if team_id > 0:
        pass  # just omit the studies on the teams view
    if member_id > 0:
        scheduled_studies = StudyRequest.objects.filter(member=_get_member(request),
                                                        state__in=["B", "D"]).order_by('slot_start', 'priority')
        studies_events = [d.get_study_as_json_event() for d in scheduled_studies]

    return HttpResponse(json.dumps(studies_events), content_type="application/json")


def get_all_studies(request: HttpRequest) -> JsonResponse:
    bookings = StudyRequest.objects.all().order_by('-booking_created')
    data = {"data": [b.study_as_datatable_json(user=request.user) for b in bookings]}
    return JsonResponse(data)
