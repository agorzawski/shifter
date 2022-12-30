from .activeshift import prepare_active_crew
from .models import Contact
from django.conf import settings
from django.db.models import Q, Count
import django.contrib.messages as messages
from members.models import Member, Team
from shifts.models import Campaign, Revision, Shift, Slot, ShifterMessage
from shifts.models import SIMPLE_DATE, MONTH_NAME, DATE_FORMAT
from shifts.hrcodes import get_public_holidays, get_date_code_counts, count_total
import os
import datetime
from guardian.shortcuts import get_users_with_perms, get_objects_for_user
from shifter.settings import MAIN_PAGE_HOME_BUTTON, APP_REPO, APP_REPO_ICON, CONTROL_ROOM_PHONE_NUMBER, WWW_EXTRA_INFO, \
    SHIFTER_PRODUCTION_INSTANCE, SHIFTER_TEST_INSTANCE, PHONEBOOK_NAME, STOP_DEV_MESSAGES, DEFAULT_SHIFT_SLOT


def operation_crew_context(request):
    active_shift = prepare_active_crew(dayToGo=None,
                                       slotToGo=None,
                                       hourToGo=None,
                                       fullUpdate=False)
    the_current_crew = active_shift['currentTeam']
    for people in the_current_crew:
        people.real_role = people.role.name if people.role is not None else people.member.role.name
    return {'operation_crew': the_current_crew}


def useful_contact_context(request):
    contacts = Contact.objects.filter(active=True)
    return {'useful_contact': contacts}


def nav_bar_context(request):
    teams = Team.objects.all().order_by('name')
    return {'teams': teams}


def rota_maker_role(request):
    rota_maker_for = get_objects_for_user(request.user, 'members.view_desiderata')
    return {'rota_maker_for': rota_maker_for}


def application_context(request):
    if SHIFTER_TEST_INSTANCE and not STOP_DEV_MESSAGES:
        messages.warning(request,
                         """<strong>This is a DEVELOPMENT instance</strong>
                         In order to find current schedules, please refer to <a href="{}">the production instance</a>
                         """.format(SHIFTER_PRODUCTION_INSTANCE)
                         )

    stream = os.popen('git describe --tags')
    git_tag = stream.read()
    context = {
        'APP_NAME': MAIN_PAGE_HOME_BUTTON,
        'APP_REPO': APP_REPO,
        'SHIFTER_TEST_INSTANCE': SHIFTER_TEST_INSTANCE,
        'APP_GIT_TAG': git_tag,
        'controlRoomPhoneNumber': CONTROL_ROOM_PHONE_NUMBER,
        'wwwWithMoreInfo': WWW_EXTRA_INFO,
    }
    return context
