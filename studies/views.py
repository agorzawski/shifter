from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from shifter.settings import LOGIN_URL
from studies.models import *
from studies.forms import StudyRequestForm, StudyRequestFormClosing
from shifts.contexts import prepare_default_context
import django.contrib.messages as messages
from django.views.decorators.http import require_safe
from django.contrib.auth.decorators import login_required


# Create your views here.
def page_not_found(request, exception):
    return render(request, "404.html", {})

@login_required(login_url=LOGIN_URL)
@require_safe
def request(request):
    form = None
    bookNew = request.GET.get('new', False)
    labelFilter = request.GET.get('typeId', False)
    typeFilter = False
    booking_states = [item[1] for item in StudyRequest.BOOKING_STATE_CHOICES]
    try:
        for ele in StudyRequest.BOOKING_STATE_CHOICES:
            if ele[1] == labelFilter:
                typeFilter = ele[0]
    except:
        typeFilter = False
    if bookNew:
        form = StudyRequestForm({'member': request.user,})
                                #'Study duration (30 min steps)': 1.5,
                                #'Max. Beam Pulse Length (us)': 6.0,
                                #'Max. Beam Pulse Length (us)': 5.0,
                                #'Beam Destination': 'LEBT FC'})
    activeBooking = None
    bookingId = request.GET.get('close', None)
    if bookingId is not None:
        try:
            activeBooking = StudyRequest.objects.get(id=bookingId)
        except Exception as e:
            messages.error(request, 'Wrong booking ID')
            return page_not_found(request, exception=e)
        if activeBooking.member != request.user: # and not request.user.is_staff:
            messages.error(request, 'You cannot close the booking that is not yours!')
            return page_not_found(request, exception=None)
        form = StudyRequestFormClosing()
    bookings = StudyRequest.objects.all().order_by('-booking_created')
    if typeFilter is not False:
        bookings = StudyRequest.objects.filter(state=typeFilter).order_by('-booking_created')
    context = {
        'form': form,
        'studyFilter': labelFilter,
        'activeBooking': activeBooking,
        'bookingStates': booking_states,
        'studyBookings': bookings,
    }
    return render(request, 'studies/request.html', prepare_default_context(request, context))

@login_required(login_url=LOGIN_URL)
@require_http_methods(["POST"])
@csrf_protect
def request_post(request):
    form = StudyRequestForm(request.POST)
    labelFilter = False
    booking_states = [item[1] for item in StudyRequest.BOOKING_STATE_CHOICES]
    bookings = StudyRequest.objects.all().order_by('-booking_created')
    if form.is_valid():
        post = form.save(commit=False)
        post.booking_created = datetime.datetime.now()
        post.booked_by = request.user
        if post.member != request.user and not request.user.is_staff:
            messages.error(request, 'You can only book for yourself! Contact OPS team to book for someone else!')
            return page_not_found(request, exception=None)
        post.save()
        message = "Study Booking {} for {} on {}, is added!".format(post.title, post.member.first_name, post.booking_created)
        messages.success(request, message)

    context = {
        'studyBookings': bookings,
        'bookingStates': booking_states,
        'studyFilter': labelFilter,
    }
    return render(request, 'studies/request.html', prepare_default_context(request, context))

@login_required(login_url=LOGIN_URL)
@require_http_methods(["POST"])
@csrf_protect
def request_post_close(request):
    print(request.POST)
    form = StudyRequestFormClosing(request.POST)
    idToUse = request.POST['activeBookingId']
    stateToUse = request.POST['bookingState']
    labelFilter = False
    booking_states = [item[1] for item in StudyRequest.BOOKING_STATE_CHOICES]
    bookings = StudyRequest.objects.all().order_by('-booking_created')
    if form.is_valid():
        post = form.save(commit=False)
        activeBooking = StudyRequest.objects.get(id=idToUse)
        activeBooking.booking_finished = datetime.datetime.now()
        activeBooking.after_comment = post.after_comment
        activeBooking.state = str(stateToUse)
        activeBooking.finished_by = request.user
        activeBooking.save()
        if (stateToUse=="D"):
            message = "Study request for {} on {}, is now closed!".format(activeBooking.member.first_name,
                                                                activeBooking.booking_created)
        else:
            message = "Study request for {} on {}, is now canceled!".format(activeBooking.member.first_name,
                                                                          activeBooking.booking_created)
        messages.success(request, message)

    context = {
        'studyBookings': bookings,
        'bookingStates': booking_states,
        'studyFilter': labelFilter,
    }
    return render(request, 'studies/request.html', prepare_default_context(request, context))
