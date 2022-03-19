from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
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

def page_not_found(request, exception):
    return render(request, "404.html", {})


@require_safe
def index(request):
    revisions = Revision.objects.filter(valid=True).order_by("-number")
    return prepare_main_page(request, revisions)


@require_http_methods(["POST"])
@csrf_protect
def index_post(request):
    revisions = Revision.objects.filter(valid=True).order_by("-number")
    revision = Revision.objects.filter(number=request.POST['revision']).first()
    # TODO implement filter on campaigns
    filtered_campaigns = None
    return prepare_main_page(request, revisions, revision=revision, filtered_campaigns=filtered_campaigns)


def prepare_main_page(request, revisions, revision=None, filtered_campaigns=None):
    if revision is None:
        revision = revisions.first()
    scheduled_shifts = Shift.objects.filter(revision=revision).order_by('date', 'slot__hour_start',
                                                                        'member__role__priority')
    scheduled_campaigns = Campaign.objects.filter(revision=revision)
    context = {
        'revisions': revisions,
        'displayed_revision': revision,
        'scheduled_shifts_list': scheduled_shifts,
        'filtered_campaigns': filtered_campaigns,
        'scheduled_campaigns_list': scheduled_campaigns,
    }
    return render(request, 'index.html', prepare_default_context(request, context))


@require_safe
def dates(request):
    context = {
        'campaigns': Campaign.objects.all(),
        'slots': Slot.objects.all().order_by('hour_start'),
        'shiftroles': ShiftRole.objects.all(),
        'memberroles': members.models.Role.objects.all(),
    }
    return render(request, 'dates.html', prepare_default_context(request, context))


@login_required
@require_http_methods(["POST"])
@csrf_protect
def dates_slots_update(request):
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
    context = {'today': activeShift['today'],
               'checkTime': activeShift['today'].time(),
               'activeSlots': activeShift['activeSlots'],
               'currentTeam': activeShift['currentTeam'],
               'shiftID': activeShift['shiftID'], }
    return render(request, 'today.html', prepare_default_context(request, context))


@require_safe
@login_required
def user(request):
    member = request.user
    return render(request, 'user.html', prepare_default_context(request,
                                                                prepare_user_context(member)))


@require_safe
def user_simple(request):
    if request.GET.get('id', None) is not None:
        member = Member.objects.filter(id=request.GET.get('id')).first()
        return render(request, 'user.html', prepare_default_context(request,
                                                                    prepare_user_context(member)))
    messages.info(request, 'Unauthorized access. Returning back to the main page!')
    return HttpResponseRedirect(reverse("shifter:index"))


@require_safe
@login_required
def team(request):
    member = request.user
    context = {'browsable': True}
    return render(request, 'team.html',
                  prepare_default_context(request,
                                          prepare_team_context(request,
                                                               member=member,
                                                               team=None,
                                                               extraContext=context)))


@require_safe
def team_simple(request):
    if request.GET.get('mid', None) is not None:
        member = Member.objects.filter(id=request.GET.get('mid')).first()
        context = {'browsable': False}
        return render(request, 'team.html',
                      prepare_default_context(request,
                                              prepare_team_context(request,
                                                                   member=member,
                                                                   team=None,
                                                                   extraContext=context)))
    if request.GET.get('id', None) is not None:
        team = Team.objects.filter(id=request.GET.get('id')).first()
        extra_context = {'browsable': False}
        return render(request, 'team.html',
                      prepare_default_context(request,
                                              prepare_team_context(request,
                                                                   member=None,
                                                                   team=team,
                                                                   extraContext=extra_context)))

    messages.info(request, 'Unauthorized access. Returning back to the main page!')
    return HttpResponseRedirect(reverse("shifter:index"))


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
    if team is not None:
        shifts = Shift.objects.filter(member__team=team, revision=revision)
    if team is None and member is None:
        shifts = Shift.objects.filter(revision=revision)

    context = {
        'campaign': 'Exported Shifts',
        'shifts': shifts,
        'member': member,
        'team': team if not None else member.team,
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
    context = {
        'campaign': 'Exported Shifts',
        'shifts': shifts,
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
    return JsonResponse(prepare_for_JSON(activeShift))


@require_safe
def shifts(request):
    shiftId = request.GET.get('id', None)
    dataToReturn = {}
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
    # add campaigns and revisions
    data = {'campaigns': Campaign.objects.all(),
            'revisions': Revision.objects.all(),
            'today': datetime.datetime.now().strftime(DATE_FORMAT)
            }

    revision = Revision.objects.filter(number=request.POST['revision']).first()
    campaign = Campaign.objects.filter(id=request.POST['camp']).first()
    oldStartDate = campaign.date_start
    newStartDate = datetime.datetime.strptime(request.POST['new-date'], DATE_FORMAT).date()
    daysDelta = newStartDate - oldStartDate
    deltaToApply = datetime.timedelta(days=daysDelta.days)
    messages.info(request, 'Found {} difference to update'.format(daysDelta))
    shifts_to_update = Shift.objects.filter(campaign=campaign, revision=campaign.revision)
    messages.info(request, 'Found {} shifts to update'.format(len(shifts_to_update)))
    doneCounter = 0
    for oldShift in shifts_to_update:
        shift = Shift()
        shift.member = oldShift.member
        shift.campaign = campaign
        shift.slot = oldShift.slot
        shift.role = oldShift.role
        tag = oldShift.csv_upload_tag
        if tag is None:
            tag = ""
        shift.csv_upload_tag = tag + '_update'
        # updated info
        shift.revision = revision
        shift.date = oldShift.date + deltaToApply
        try:
            shift.save()
            doneCounter += 1
        except Exception:
            messages.error(request, 'Cannot update old shift {}, skipping!'.format(oldShift))

    # at last, update the actual campaign data
    campaign.revision = revision
    campaign.date_start = campaign.date_start + deltaToApply
    campaign.date_end = campaign.date_end + deltaToApply
    campaign.save()
    messages.info(request, 'Done OK with {} shifts'.format(doneCounter))
    return HttpResponseRedirect(reverse("shifter:shift-update"))


@require_safe
@login_required
def shifts_upload(request):
    data = {'campaigns': Campaign.objects.all(),
            'revisions': Revision.objects.all(),
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


@login_required
@require_safe
def assets(request):
    form = None
    bookNew = request.GET.get('new', False)
    if bookNew:
        form = AssetBookingForm({'member': request.user,
                                 'use_start': datetime.datetime.now().strftime(DATE_FORMAT_FULL),
                                 'use_end': datetime.datetime.now().strftime(DATE_FORMAT_FULL)})
    activeBooking = None
    bookingId = request.GET.get('close', None)
    if bookingId is not None:
        try:
            activeBooking = AssetBooking.objects.get(id=bookingId)
        except Exception as e:
            messages.error(request, 'Wrong booking ID')
            return page_not_found(request, exception=e)
        if activeBooking.member != request.user and not request.user.is_staff:
            messages.error(request, 'You cannot close the booking that is not yours!')
            return page_not_found(request, exception=None)
        form = AssetBookingFormClosing()

    context = {
        'form': form,
        'activeBooking': activeBooking,
        'assetbookings': AssetBooking.objects.all().order_by('-use_start'),
    }
    return render(request, 'assets.html', prepare_default_context(request, context))


@login_required
@require_http_methods(["POST"])
@csrf_protect
def assets_post(request):
    form = AssetBookingForm(request.POST)
    if form.is_valid():
        post = form.save(commit=False)
        post.booking_created = datetime.datetime.now()  # timezone.now()
        post.booked_by = request.user
        if post.member != request.user and not request.user.is_staff:
            messages.error(request, 'You can only book for yourself! Contact OPS team to book for someone else!')
            return page_not_found(request, exception=None)
        post.save()
        message = "Booking for {} on {}, is added!".format(post.member.first_name, post.use_start)
        messages.success(request, message)

    context = {
        'assetbookings': AssetBooking.objects.all().order_by('-use_start'),
    }
    return render(request, 'assets.html', prepare_default_context(request, context))


@login_required
@require_http_methods(["POST"])
@csrf_protect
def assets_post_close(request):
    print(request.POST)
    form = AssetBookingFormClosing(request.POST)
    idToUse = request.POST['activeBookingId']
    if form.is_valid():
        post = form.save(commit=False)
        activeBooking = AssetBooking.objects.get(id=idToUse)
        activeBooking.booking_finished = datetime.datetime.now()
        activeBooking.after_comment = post.after_comment
        activeBooking.state = AssetBooking.BookingState.RETURNED
        activeBooking.finished_by = request.user
        activeBooking.save()
        message = "Booking for {} on {}, is now closed!".format(activeBooking.member.first_name,
                                                                activeBooking.use_start)
        messages.success(request, message)

    context = {
        'assetbookings': AssetBooking.objects.all().order_by('-use_start'),
    }
    return render(request, 'assets.html', prepare_default_context(request, context))
