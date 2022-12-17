from django.db.models import Q, Count
import django.contrib.messages as messages
from members.models import Member, Team
from shifts.models import Campaign, Revision, Shift, Slot, ShifterMessage
from studies.models import StudyRequest
from shifts.models import SIMPLE_DATE, MONTH_NAME, DATE_FORMAT
from shifts.hrcodes import get_public_holidays, get_date_code_counts, count_total
import os
import datetime
from guardian.shortcuts import get_users_with_perms, get_objects_for_user
from shifter.settings import MAIN_PAGE_HOME_BUTTON, APP_REPO, APP_REPO_ICON, CONTROL_ROOM_PHONE_NUMBER, WWW_EXTRA_INFO, \
    SHIFTER_PRODUCTION_INSTANCE, SHIFTER_TEST_INSTANCE, PHONEBOOK_NAME, STOP_DEV_MESSAGES, DEFAULT_SHIFT_SLOT


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
    if SHIFTER_TEST_INSTANCE and not STOP_DEV_MESSAGES:
        messages.info(request,
                      '<h4> <span class="badge bg-danger">ATTENTION!</span> </h4> \
                       <strong>This is a DEVELOPMENT instance</strong>. <br>\
                       In order to find current schedules, please refer to <a href="{}">the production instance</a>'
                      .format(SHIFTER_PRODUCTION_INSTANCE), )
    for oneShifterMessages in ShifterMessage.objects.filter(valid=True).order_by('-number'):
        messages.warning(request, oneShifterMessages.description)

    rota_maker_for = get_objects_for_user(request.user, 'members.view_desiderata')

    context = {
        'logged_user': request.user.is_authenticated,
        'defaultDate': date.strftime(DATE_FORMAT),
        'slots': Slot.objects.all().order_by('hour_start'),
        'teams': Team.objects.all().order_by('name'),
        'latest_revision': latest_revision,
        'displayed_revision': latest_revision,
        'APP_NAME': MAIN_PAGE_HOME_BUTTON,
        'APP_REPO': APP_REPO,
        'APP_REPO_ICON': APP_REPO_ICON,
        'PHONEBOOK_NAME': PHONEBOOK_NAME,
        'SHIFTER_TEST_INSTANCE': SHIFTER_TEST_INSTANCE,
        'APP_GIT_TAG': GIT_LAST_TAG,
        'controlRoomPhoneNumber': CONTROL_ROOM_PHONE_NUMBER,
        'DEFAULT_SHIFT_SLOT': Slot.objects.get(abbreviation=DEFAULT_SHIFT_SLOT),
        'wwwWithMoreInfo': WWW_EXTRA_INFO,
        'rota_maker_for': rota_maker_for,
    }
    for one in contextToAdd.keys():
        context[one] = contextToAdd[one]
    return context


def prepare_user_context(member, revisionNext=None):
    currentMonth = datetime.datetime.now()
    nextMonth = currentMonth + datetime.timedelta(30)  # banking rounding
    revision = Revision.objects.filter(valid=True).order_by("-number").first()
    newer_revisions = Revision.objects.filter(date_start__gt=revision.date_start).order_by("-number")
    scheduled_shifts = Shift.objects.filter(member=member, revision=revision).order_by("-date")
    # scheduled_studies = StudyRequest.objects.filter(member=member,state__in=["B","D"]).order_by('slot_start', 'priority')
    shift2codes = get_date_code_counts(scheduled_shifts)
    scheduled_campaigns = Campaign.objects.all().filter(revision=revision)
    context = {
        'member': member,
        'currentmonth': currentMonth.strftime(MONTH_NAME),
        'nextmonth': nextMonth.strftime(MONTH_NAME),
        'scheduled_campaigns_list': scheduled_campaigns,
        'newer_revisions': newer_revisions,
        'campaigns': Campaign.objects.filter(revision=revision),
        'hrcodes': shift2codes,
        'hrcodes_summary': count_total(shift2codes)
    }
    return context


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


def prepare_team_context(request, member=None, team=None, extraContext=None):
    currentMonth = datetime.datetime.now()
    if request.GET.get('date'):
        currentMonth = datetime.datetime.strptime(request.GET['date'], SIMPLE_DATE)
    nextMonth = currentMonth + datetime.timedelta(31)  # banking rounding
    lastMonth = currentMonth - datetime.timedelta(31)
    revision = Revision.objects.filter(valid=True).order_by("-number").first()
    if team is None and Member is not None:
        team = member.team
    teamMembers = Member.objects.filter(team=team)
    scheduled_shifts = Shift.objects.filter(member__team=team, revision=revision)
    scheduled_studies = StudyRequest.objects.filter(state__in=["B","D"],member__team=team).order_by('slot_start', 'priority')
    scheduled_campaigns = Campaign.objects.all().filter(revision=revision)
    # TODO get this outside the main code, maybe another flag in the Slot? TBC
    slotLookUp = ['NWH', 'PM', 'AM', 'EV', 'NG', 'LMS', 'LES', 'D', 'A']
    validSlots = Slot.objects.filter(abbreviation__in=slotLookUp).order_by('hour_start')
    teamMembersSummary = []
    for m in teamMembers:
        l, result = get_shift_summary(m, validSlots, revision, currentMonth)
        memberSummary = [m, l]
        for oneSlot in validSlots:
            memberSummary.append(result.get(oneSlot.abbreviation, '--'))
        teamMembersSummary.append(memberSummary)

    rota_maker = get_users_with_perms(team, only_with_perms_in=['view_desiderata'])
    context = {
        'member': member,
        'team': team,
        'teamMembers': teamMembersSummary,
        'validSlots': validSlots,
        'currentmonth_label': currentMonth.strftime(MONTH_NAME),
        'nextmonth': nextMonth.strftime(SIMPLE_DATE),
        'lastmonth': lastMonth.strftime(SIMPLE_DATE),
        'nextmonth_label': nextMonth.strftime(MONTH_NAME),
        'lastmonth_label': lastMonth.strftime(MONTH_NAME),
        'campaigns': Campaign.objects.filter(revision=revision),
        'scheduled_shifts_list': scheduled_shifts,
        'scheduled_studies_list': scheduled_studies,
        'scheduled_campaigns_list': scheduled_campaigns,
        'rota_maker': rota_maker,
    }
    if isinstance(extraContext, dict):
        for one in extraContext.keys():
            context[one] = extraContext[one]
    return context
