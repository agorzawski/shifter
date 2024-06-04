$(document).ready(function() {
    $('#shiftswap_date_range_picker').daterangepicker({
        opens: 'left',
    });

    $('#shiftswap_date_range_picker').on('change', function() {
        $('#table_shiftswap').DataTable().ajax.reload();
    });
    $('#table_shiftswap').DataTable({
        ajax: {
            url: $('#table_shiftswap').data('source'),
            data: function(d) {
                d.start = $('#shiftswap_date_range_picker').data('daterangepicker').startDate.format('YYYY-MM-DD');
                d.end = $('#shiftswap_date_range_picker').data('daterangepicker').endDate.format('YYYY-MM-DD');
                d.team = $("team_id").data('id');
            },
        },
        dom: 'P',
        bPaginate: false,
        paging: false,
//        searchPanes: {
//            initCollapsed: true
//        },
        "columns": [{
                searchPanes: {
                    show: false
                }
            },
            {
                searchPanes: {
                    show: false
                }
            },
            {
//                visible:true,
                searchPanes: {
                    show: false
                }
            },
            {
                searchPanes: {
                    show: false
                }
            },
        ],
        "autoWidth": false,
    });
});