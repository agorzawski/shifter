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
    let future_rev_tag = $("[name='future_revisions_checkboxes']")
    if( future_rev_tag.length){
        return $("input[name='future_revisions_checkboxes']:checked").data('future_rev_id');
    }else{
        return -1;
    }
}

function get_specific_users(){
    if(document.getElementById('users_selection') !== null){
        return $(".users_selection").val();
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
    $('#table_id').DataTable({
        searching: true,
        paging: false,
        ordering: true,
    });

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
      datesSet: function(date){
          // Here fetch data for shifts breakdown
            $.ajax({
              method: "GET",
              url: $('#table_id').data('content_url'),
              data: { start: date.startStr, end: date.endStr},
              success: function(data){
                    $('#table_id').dataTable().fnClearTable();
                    $('#table_id').dataTable().fnAddData(data.data);
                    $('#table_id caption').html(data.header);
              },

            })


      },
      eventSources: [
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
            users: get_specific_users(),
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

    },
    {
      id: "studies",
      url: $('#calendar').data('source-studies'),
      extraParams: function() {
          return {
            show_studies: $('#show_studies').is(':checked'),
            team: get_team_id(),
            member: get_member_id(),
          };
        },
      failure: function() {
        alert('there was an error while fetching studies planning!');
      },
    }

  ],
    });
    calendar.render();

    $('#all_roles').change(function() {
        calendar.getEventSourceById('shifts').refetch()
    });

    $('#show_studies').change(function() {
        calendar.getEventSourceById('studies').refetch()
    });

    $(".users_selection").change( function() {
        calendar.getEventSourceById('shifts').refetch()
    });

    $(".displayed_campaigns").change( function() {
        calendar.getEventSourceById('shifts').refetch()
    });

    $('#planning-tab').click(function(){
        calendar.render()
    })

    $('input[type=radio][name=future_revisions_checkboxes]').change(function() {
        calendar.getEventSourceById('shifts').refetch()
    })

});
