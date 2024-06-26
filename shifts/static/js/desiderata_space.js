$(document).ready(function() {
    $('#date_range_picker').daterangepicker({
        opens: 'left',
    });

    $('#date_range_picker').on('change', function() {
        $('#table_HR').DataTable().ajax.reload();
    });
    $('#table_HR').DataTable({
        ajax: {
            url: $('#table_HR').data('source'),
            data: function(d) {
                d.start = $('#date_range_picker').data('daterangepicker').startDate.format('YYYY-MM-DD');
                d.end = $('#date_range_picker').data('daterangepicker').endDate.format('YYYY-MM-DD');
                d.team = $("team_id").data('id');
            },
        },
        dom: 'P',
        bPaginate: false,
        paging: false,
        searchPanes: {
            initCollapsed: true
        },
        "columns": [{
                searchPanes: {
                    show: false
                }
            },
            {
                visible:true,
                searchPanes: {
                    show: true
                }
            },
            {
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
                searchPanes: {
                    show: false
                }
            },
        ],
        "autoWidth": false,
        footerCallback: function(row, data, start, end, display) {
            var api = this.api();

            // Remove the formatting to get integer data for summation
            var intVal = function(i) {
                return typeof i === 'string' ? i.replace(/[\$,]/g, '') * 1 : typeof i === 'number' ? i : 0;
            };

            // Total over all pages
            ob1 = api.column(2)
                .data()
                .reduce(function(a, b) {
                    return intVal(a) + intVal(b);
                }, 0);

            ob1Total = api
                .column(2, {
                    page: 'current'
                })
                .data()
                .reduce(function(a, b) {
                    return intVal(a) + intVal(b);
                }, 0);

            ob2 = api.column(3)
                .data()
                .reduce(function(a, b) {
                    return intVal(a) + intVal(b);
                }, 0);

            ob2Total = api
                .column(3, {
                    page: 'current'
                })
                .data()
                .reduce(function(a, b) {
                    return intVal(a) + intVal(b);
                }, 0);

            ob3 = api.column(4)
                .data()
                .reduce(function(a, b) {
                    return intVal(a) + intVal(b);
                }, 0);

            ob3Total = api
                .column(4, {
                    page: 'current'
                })
                .data()
                .reduce(function(a, b) {
                    return intVal(a) + intVal(b);
                }, 0);


            ob4 = api.column(5)
                .data()
                .reduce(function(a, b) {
                    return intVal(a) + intVal(b);
                }, 0);

            ob4Total = api
                .column(5, {
                    page: 'current'
                })
                .data()
                .reduce(function(a, b) {
                    return intVal(a) + intVal(b);
                }, 0);

            nwh = api.column(6)
                .data()
                .reduce(function(a, b) {
                    return intVal(a) + intVal(b);
                }, 0);

            nwhTotal = api
                .column(6, {
                    page: 'current'
                })
                .data()
                .reduce(function(a, b) {
                    return intVal(a) + intVal(b);
                }, 0);
            // Update footer
            $(api.column(2).footer()).html(ob1Total + ' hours (' + ob1 + 'h total)');
            $(api.column(3).footer()).html(ob2Total + ' hours (' + ob2 + 'h total)');
            $(api.column(4).footer()).html(ob3Total + ' hours (' + ob3 + 'h total)');
            $(api.column(5).footer()).html(ob4Total + ' hours (' + ob4 + 'h total)');
            $(api.column(6).footer()).html(nwhTotal + ' hours (' + nwh + 'h total)');
        },




    });

});