function get_selected_campaigns(){
    return $(".displayed_campaigns").val();
}

function get_revision(){
    if(document.getElementById('displayed_revision') !== null){
        return $(".displayed_revision").val();
    }else{
        return -1;
    }
}

function get_revision_next(){
    let future_rev_tag = $("future_rev_id")
    if( future_rev_tag.length){
        return future_rev_tag.data("id");
    }else{
        return -1;
    }
}

function get_team_id(){
    let team_tag = $("#team_id_for_ajax")
    if( team_tag.length){
        return team_tag.data("id");
    }else{
        return -1;
    }
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
    let calendarEl = document.getElementById('calendar');
    let calendar = new FullCalendar.Calendar(calendarEl, {
      themeSystem: 'bootstrap5',
      customButtons: {
              myCustomButton: {
                  text: 'Tools',
                  click: function() {
                        myOffcanvas = $('#tools_off_canvas')
                        var bsOffcanvas = new bootstrap.Offcanvas(myOffcanvas)
                        bsOffcanvas.show()
                  }
    }
      },
      headerToolbar: { left: 'prev,today,next',
                center:'title',
                right: 'myCustomButton dayGridMonth,timeGridWeek',
              },
      //initialView: 'dayGridWeek', //TODO
      columnFormat: {
            month: 'ddd',
            week: 'ddd M/d',
        },
      initialDate: $('#calendar').data('default-date'),
      weekNumbers: true,
      navLinks: true, // can click day/week names to navigate views
      editable: false,
      firstDay:1, // Monday
      businessHours: [
         {
          daysOfWeek: [ 1, 2, 3, 4, 5 ],
           startTime: '08:00', // 8am
           endTime: '18:00' // 6pm
         },],
      eventLimit: true, // allow 'more' link when too many events
      eventDisplay: 'block',
      eventOrder: "start,id,name,title",
      eventSources: [

    // your event source
    {
      id: "shifts",
      url: $('#calendar').data('source-shifts'),
      extraParams: function() {
          return {
            all_roles: $('#all_roles').is(':checked'),
            revision: get_revision(),
            revision_next: get_revision_next(),
            campaigns: get_selected_campaigns(),
            team: get_team_id(),
            member: get_member_id(),
          };
        },
      failure: function() {
        alert('there was an error while fetching events!');
      },

    },
    {
      id: "holidays",
      url: $('#calendar').data('source-holidays'),
      failure: function() {
        alert('there was an error while fetching public holidays!');
      },

    }
  ],
    });
    calendar.render();

    $('#all_roles').change(function() {
        calendar.getEventSourceById('shifts').refetch()
    });

    $('#displayed_revision').change(function() {
        calendar.getEventSourceById('shifts').refetch()
        //get revision name :
                $.ajax({
                url: $('#calendar').data('source-revision'),
                data: {'revision' : $('#revision').find(":selected").val()},
                success: function(data){
                    var div_to_change = $('#displayed_revision_name')
                    div_to_change.empty()
                    div_to_change.html(data.name)
                },
        });

    });

    $(".displayed_campaigns").change( function() {
        calendar.getEventSourceById('shifts').refetch()
    });
});