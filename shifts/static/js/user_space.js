getUrlParameter = function getUrlParameter(sParam) {
    var sPageURL = window.location.search.substring(1),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : decodeURIComponent(sParameterName[1]);
        }
    }
    return false;
};


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
            },
        },
        "autoWidth": false,
        buttons: [{
            extend: 'collection',
            text: 'Export',
            buttons: ['copy', 'csv',]
        }],
        dom: 'Bfrtip',
        pageLength: 25,
        footerCallback: function(row, data, start, end, display) {
            var api = this.api();

            // Remove the formatting to get integer data for summation
            var intVal = function(i) {
                return typeof i === 'string' ? i.replace(/[\$,]/g, '') * 1 : typeof i === 'number' ? i : 0;
            };

            // Total over all pages
            ob1 = api.column(1)
                .data()
                .reduce(function(a, b) {
                    return intVal(a) + intVal(b);
                }, 0);

            ob1Total = api
                .column(1, {
                    page: 'current'
                })
                .data()
                .reduce(function(a, b) {
                    return intVal(a) + intVal(b);
                }, 0);

            ob2 = api.column(2)
                .data()
                .reduce(function(a, b) {
                    return intVal(a) + intVal(b);
                }, 0);

            ob2Total = api
                .column(2, {
                    page: 'current'
                })
                .data()
                .reduce(function(a, b) {
                    return intVal(a) + intVal(b);
                }, 0);

            ob3 = api.column(3)
                .data()
                .reduce(function(a, b) {
                    return intVal(a) + intVal(b);
                }, 0);

            ob3Total = api
                .column(3, {
                    page: 'current'
                })
                .data()
                .reduce(function(a, b) {
                    return intVal(a) + intVal(b);
                }, 0);


            ob4 = api.column(4)
                .data()
                .reduce(function(a, b) {
                    return intVal(a) + intVal(b);
                }, 0);

            ob4Total = api
                .column(4, {
                    page: 'current'
                })
                .data()
                .reduce(function(a, b) {
                    return intVal(a) + intVal(b);
                }, 0);

            nwh = api.column(5)
                .data()
                .reduce(function(a, b) {
                    return intVal(a) + intVal(b);
                }, 0);

            nwhTotal = api
                .column(5, {
                    page: 'current'
                })
                .data()
                .reduce(function(a, b) {
                    return intVal(a) + intVal(b);
                }, 0);
            // Update footer
            $(api.column(1).footer()).html(ob1Total + ' hours (' + ob1 + 'h total)');
            $(api.column(2).footer()).html(ob2Total + ' hours (' + ob2 + 'h total)');
            $(api.column(3).footer()).html(ob3Total + ' hours (' + ob3 + 'h total)');
            $(api.column(4).footer()).html(ob4Total + ' hours (' + ob4 + 'h total)');
            $(api.column(5).footer()).html(nwhTotal + ' hours (' + nwh + 'h total)');
        },




    });

    const toastLiveExample = document.getElementById('live_toast')

    var open_links = getUrlParameter('ical');
    if (open_links) {
        const triggerTabList = document.querySelectorAll('#user_tabs button')
        triggerTabList.forEach(triggerEl => {
            const tabTrigger = new bootstrap.Tab(triggerEl)

            triggerEl.addEventListener('click', event => {
                event.preventDefault()
                tabTrigger.show()
            })
        })


        const triggerEl = document.querySelector('#user_tabs button[data-bs-target="#links-tab-pane"]')
        bootstrap.Tab.getInstance(triggerEl).show() // Select tab by name
    }

    var open_links = getUrlParameter('swaps');
    if (open_links) {
        const triggerTabList = document.querySelectorAll('#user_tabs button')
        triggerTabList.forEach(triggerEl => {
            const tabTrigger = new bootstrap.Tab(triggerEl)

            triggerEl.addEventListener('click', event => {
                event.preventDefault()
                tabTrigger.show()
            })
        })


        const triggerEl = document.querySelector('#user_tabs button[data-bs-target="#shift-swap-tab-pane"]')
        bootstrap.Tab.getInstance(triggerEl).show() // Select tab by name
    }

    var open_links = getUrlParameter('notifications');
    if (open_links) {
        const triggerTabList = document.querySelectorAll('#user_tabs button')
        triggerTabList.forEach(triggerEl => {
            const tabTrigger = new bootstrap.Tab(triggerEl)

            triggerEl.addEventListener('click', event => {
                event.preventDefault()
                tabTrigger.show()
            })
        })


        const triggerEl = document.querySelector('#user_tabs button[data-bs-target="#notify-tab-pane"]')
        bootstrap.Tab.getInstance(triggerEl).show() // Select tab by name
    }


    $("#personal_link_clipboard").click(function() {
        navigator.clipboard.writeText($('#personal_link_clipboard_data').val()).then(function() {
            $('#toast_content').text('Data copied to clipboard. User Ctrl+P to paste data.')



        }, function() {
            $('#toast_content').text('Failure to copy. Check permissions for clipboard')
        });
        const toast = new bootstrap.Toast(toastLiveExample)
        toast.show()

    });

    $("#team_link_clipboard").click(function() {
        navigator.clipboard.writeText($('#team_link_clipboard_data').val()).then(function() {
            $('#toast_content').text('Data copied to clipboard. User Ctrl+P to paste data.')


        }, function() {
            $('#toast_content').text('Failure to copy. Check permissions for clipboard')
        });
        const toast = new bootstrap.Toast(toastLiveExample)
        toast.show()
    });

});