function get_desiderata_type(){
    return $("#desiderata_type_form input[type='radio']:checked").val();
}

function get_team_desiderata_status(){
    return $('#showsTeamDesiderata').prop('checked');
}

function get_my_shifts_status(){
    return $('#showMyShifts').prop('checked');
}

function get_member_id(){
    let member_tag = $("member_id")
    if( member_tag.length){
        return member_tag.data("id");
    }else{
        return -1;
    }
}

$(document).ready(function () {
    $('#showsTeamDesiderata').on('change', function() {
        calendar.getEventSourceById('team_desiderata').refetch()
    })

    $('#showMyShifts').on('change', function() {
        calendar.getEventSourceById('shifts').refetch()
    })


    let calendarEl = document.getElementById('calendar');
    let calendar = new FullCalendar.Calendar(calendarEl, {
        timeZone: 'Europe/Stockholm',
        themeSystem: 'bootstrap5',
        headerToolbar:
            {
                left: 'prev,today,next',
                center:'title',
                right: 'dayGridMonth,timeGridWeek',
            },
        columnFormat:
            {
                month: 'ddd',
                week: 'ddd M/d',
            },
        initialDate: $('#calendar').data('default-date'),
        weekNumbers: true,
        navLinks: true, // can click day/week names to navigate views
        editable: true,
        selectHelper: true,
        selectable: true,
        selectMirror: true,
        snapDuration: '00:30:00',
        select: function(info)
        {
            $.ajax({
                url: $('#calendar').data('post-event'),
                data:
                    {
                        "allDay": info.allDay,
                        "startStr": info.startStr,
                        "endStr": info.endStr,
                        "event_type": get_desiderata_type(),
                    },
                success: function(response)
                    {
                        calendar.unselect();
                        calendar.getEventSourceById('desiderata').refetch();
                    },
                });
        },
        eventDrop: function(info)
        {
            $.ajax({
                url: $('#calendar').data('edit-event'),
                data:
                    {
                        "allDay": info.event.allDay,
                        "startStr": info.event.startStr,
                        "endStr": info.event.endStr,
                        "id": info.event.id
                    },
                success: function(response)
                    {
                        calendar.getEventSourceById('desiderata').refetch()
                    },
                error: function(response)
                    {
                        info.revert();
                    },
            });
        },
        eventClick: function(info)
        {
            if (info.event.backgroundColor !== '#fcba03') {
                info.jsEvent.preventDefault(); // don't let the browser navigate
                $.ajax({
                    url: $('#calendar').data('delete-event'),
                    data:
                        {
                            "id": info.event.id
                        },
                    success: function (response) {
                        calendar.getEventSourceById('desiderata').refetch()
                    },
                });
            }
        },
        eventResize: function(info)
        {
            $.ajax({
            url: $('#calendar').data('edit-event'),
            data:
                {
                    "allDay": info.event.allDay,
                    "startStr": info.event.startStr,
                    "endStr": info.event.endStr,
                    "id": info.event.id
                },
            success: function(response)
                {
                    calendar.getEventSourceById('desiderata').refetch()
                },
            error: function(response)
                {
                    info.revert();
                },
            });
        },
        firstDay:1, // Monday
        businessHours:
            [
                {
                    daysOfWeek: [ 1, 2, 3, 4, 5 ],
                    startTime: '08:00', // 8am
                    endTime: '18:00' // 6pm
                },
            ],
        eventLimit: true, // allow 'more' link when too many events
        eventDisplay: 'block',
        eventOrder: "start,id,name,title",
        eventSources:
            [
                {
                    id: "desiderata",
                    url: $('#calendar').data('source-desiderata'),
                    failure: function()
                    {
                        alert('there was an error while fetching desiderata!');
                    },
                },
                {
                    id: "holidays",
                    url: $('#calendar').data('source-holidays'),
                    failure: function()
                    {
                        alert('there was an error while fetching public holidays!');
                    },
                },
                {

                    id: "team_desiderata",
                    url: $('#calendar').data('source-team-desiderata'),
                    extraParams: function() {
                      return {
                        show: get_team_desiderata_status(),
                      };
                    },
                    editable: false,
                    failure: function()
                    {
                        alert('there was an error while fetching team desiderata!');
                    },
                },
                {
                  id: "shifts",
                  url: $('#calendar').data('source-shifts'),
                  extraParams: function() {
                      return {
                        all_roles: true,
                        all_states: true,
                        companion: false,
                        revision: -1,
                        member: get_member_id(),
                        show: get_my_shifts_status(),
                      };
                    },
                  failure: function() {
                    alert('there was an error while fetching events!');
                  },
                },
            ],
    });
    calendar.render();
});