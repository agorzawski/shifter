from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from studies.models import *
from studies.forms import StudyRequestForm, StudyRequestFormClosing
import django.contrib.messages as messages
from django.views import View


def page_not_found(request, exception):
    return render(request, "404.html", {})


class StudyView(View):
    def get(self, request):
        form = StudyRequestForm({'member': request.user}, user=request.user)
        closing_form = StudyRequestFormClosing()
        return render(request, 'request.html', {'form': form, 'closing_form': closing_form})

    def post(self, request):
        form = StudyRequestForm(request.POST, user=request.user)
        if form.is_valid():
            col = form.cleaned_data['collaborators']
            post = form.save(commit=False)
            post.booking_created = datetime.datetime.now()
            post.booked_by = request.user
            post.save()
            post.collaborators.set(col)
            message = "Study Booking {} for {} on {}, is added!".format(post.title, post.member.first_name, post.booking_created)
            messages.success(request, message)
        else:
            message = "Study form is not valid, please correct."
            messages.success(request, message)
        return redirect('studies:study_request')


@require_http_methods(["POST"])
def studies_close(request):
    booking_id = request.POST.get('booking_id')
    form = StudyRequestFormClosing(request.POST)
    if form.is_valid():
        comment = form.cleaned_data['after_comment']
        link = form.cleaned_data['logbook_link']
        status = form.cleaned_data['status']
        current_booking = get_object_or_404(StudyRequest, id=booking_id)
        current_booking.booking_finished = datetime.datetime.now()
        current_booking.after_comment = comment
        current_booking.logbook_link = link
        current_booking.state = status
        current_booking.finished_by = request.user
        current_booking.save()
        message = "Booking for {} on {}, was updated!".format(current_booking.member.first_name,
                                                                current_booking.title)
        messages.success(request, message)
    else:
        message = "Booking form is not valid, please correct."
        messages.success(request, message)
    return redirect('studies:study_request')
