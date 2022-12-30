$(document).ready(function () {
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
        eventColor: '#ab4646',
        select: function(info)
        {
            $.ajax({
                url: $('#calendar').data('post-event'),
                data:
                    {
                        "allDay": info.allDay,
                        "startStr": info.startStr,
                        "endStr": info.endStr
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
            info.jsEvent.preventDefault(); // don't let the browser navigate
            $.ajax({
            url: $('#calendar').data('delete-event'),
            data:
                {
                    "id": info.event.id
                },
            success: function(response)
                {
                    calendar.getEventSourceById('desiderata').refetch()
                },
            });
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
                }
            ],
    });
    calendar.render();
});