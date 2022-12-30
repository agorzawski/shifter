function get_team_id(){
    let team_tag = $("team_id")
    if( team_tag.length)
    {
        return team_tag.data("id");
    }
    else
    {
        return -1;
    }
}

$(document).ready(function () {
    let calendarEl = document.getElementById('calendar');
    let calendar = new FullCalendar.Calendar(calendarEl,
        {
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
            editable: false,
            selectHelper: false,
            selectable: false,
            selectMirror: false,
            snapDuration: '00:30:00',
            eventColor: '#ab4646',
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
                        extraParams: function()
                            {
                                return{
                                        team: get_team_id(),
                                };
                            },
                        failure: function()
                            {
                                alert('there was an error while fetching events!');
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