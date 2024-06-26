function test(event) {
    $('#closing_booking_modal').modal('show');
    $("#closed_booking_id_to_set").val($(event.target).data('book_id'))
    $("#asset_title").html("Close booking for : " + $(event.target).data('name'))

}

$(document).ready(function() {
    $('#table_id').DataTable({
        "ajax": $('#table_id').data('content_url'),
        dom: 'Plfrtip',
        order: [[3, 'desc']],
        pageLength: 25,
        searchPanes: {
            initCollapsed: true
        },
        "columns": [{
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
                data: "active",
                visible:false,
                searchPanes: {
                    show: true
                }
            },
            {
                data: "asset",
                render: {
                    _: function(data, type, row) {
                        return data.name + '<br><i><small>' + data.type + '</i></small>';
                    },
                    sp: function(data, type, row) {
                        return data.type;
                    },
                },
                searchPanes: {
                    orthogonal: 'sp',
                    show: true,
                    header: 'Asset Type',
                }
            },
            {
                data: "use_start",
                render: {
                    _: 'display',
                    sort: 'order',
                },
                searchPanes: {
                    show: false
                }
            },
            {
                data: "use_end",
                render: {
                    _: 'display',
                    sort: 'order',
                },
                searchPanes: {
                    show: false
                }
            },
            {
                data: "comment",
                searchPanes: {
                    show: false
                }
            },
            {
                data: "closing",
                searchPanes: {
                    show: false
                }
            },
        ],

    });
});