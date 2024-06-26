function test(event) {
    $('#closing_booking_modal').modal('show');
    $("#closed_booking_id_to_set").val($(event.target).data('book_id'))
    $("#asset_title").html("Edit study request for : " + $(event.target).data('name'))
}

$(document).ready(function() {
    $('#table_id').DataTable({
        "ajax": $('#table_id').data('content_url'),
        dom: 'Plfrtip',
        order: [[0, 'desc']],
        pageLength: 25,
        searchPanes: {
            initCollapsed: true
        },
        "columns": [{
              data: "id",
                render: {
                    _: function(data, type, row) {
                        return '<a class="link" href="' + data + '">' + data + '</a>';
                    },
                },
              searchPanes: {
                    show: false
                }
            },
            {
                data: "who",
                render: {
                    _: function(data, type, row) {
                        return data.member + '<br><i><small>' + data.team + '</i></small>';
                    },
                },
                searchPanes: {
                    show: false
                }
            },
            {
              data: "collaborators",
              searchPanes: {
                    show: false
                }
            },
            {
                data: "title",
                searchPanes: {
                    show: false
                }
            },
            {
                data: "description",
                width: "15%",
                searchPanes: {
                    show: false
                }
            },
            {
                data: "request_start",
                render: {
                    _: 'display',
                    sort: 'order',
                },
                searchPanes: {
                    show: false
                }
            },
            {
                data: "request_end",
                render: {
                    _: 'display',
                    sort: 'order',
                },
                searchPanes: {
                    show: false
                }
            },
            {
                data: "state",
                render: {
                    _: 'display',
                    sort: 'order',
                },
                searchPanes: {
                    show: true
                }
            },
            {
                data: "booking",
                searchPanes: {
                    show: false
                }
            },
        ],

    });
});