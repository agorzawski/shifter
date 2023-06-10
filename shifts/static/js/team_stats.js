function fill_plots(){
    var dStart = $('#stat_date_range_picker').data('daterangepicker').startDate.format('YYYY-MM-DD');
    var dEnd = $('#stat_date_range_picker').data('daterangepicker').endDate.format('YYYY-MM-DD');
    var teamId = $("team_id").data('id');
    var chart = new Highcharts.Chart({chart: {
                               renderTo: 'statBars',
                               type: 'column',
                               events: {
                                  load() {
                                    const chart = this;
                                    chart.showLoading('Loading data ...');
                                    }
                                 }
                                 }
                              });
    var chart = new Highcharts.Chart({chart: {
                    renderTo: 'statWheel',
                    type: 'dependencywheel',
                    events: {
                       load() {
                        const chart = this;
                        chart.showLoading('Loading data ...');
                        }
                      }
                    }
                  });
    // fetch bar plot stats
    $.ajax({
      dataType: "json",
      method: "GET",
      url: $('#statBars').data('content_url'),
      data: { start: dStart, end: dEnd},
      success: function(dataJSON){
            var options = {
                chart: {
                    renderTo: 'statBars',
                    type: 'column',
                },
                title: {
                    text: dataJSON.header
                },
              xAxis: {
                categories: ['OP Morning', 'Normal Working Hours', 'Afternoon', 'OP Nights'],
                labels: {
                  x: -10
                }
              },
              yAxis: {
                allowDecimals: false,
                title: {
                  text: 'Amount'
                }
              },
              series: [{},{},{},{},{},{},{},{},{},{},{},{},{},],
            };
            var arrayLength = dataJSON.data.length;
            for (var i = 0; i < arrayLength; i++) {
                options.series[i].name=dataJSON.data[i][0];
                options.series[i].data=dataJSON.data[i].slice(2,6);
            }
            var chart = new Highcharts.Chart(options);
            $('#statBarProgress').hide();
      },
      failure: function() {
            alert('there was an error while fetching stats!');
          },
    })
    // fetch wheel plot stats
     $.ajax({
      dataType: "json",
      method: "GET",
      url: $('#statWheel').data('content_url'),
      data: { start: dStart, end: dEnd, teamId: teamId, statType:'workWith'},
      success: function(dataJSON){
            var options = {
                chart: {
                    renderTo: 'statWheel',
                    type: 'dependencywheel',
                },
                title: {
                    text: dataJSON.header
                },
                accessibility: {
                    point: {
                      valueDescriptionFormat: '{index}.  {point.from} with {point.to}: {point.weight}.'
                    }
                },
                series: [{keys: ['from', 'to', 'weight'], data:  dataJSON.data}],
                dataLabels: {
                  color: '#333',
                  style: {
                    textOutline: 'none'
                  },
                  textPath: {
                    enabled: true
                  },
                  distance: 10
                },
                size: '95%'
            };
            var chart = new Highcharts.Chart(options);
            $('#statWheelProgress').hide();
      },
      failure: function() {
            alert('there was an error while fetching stats!');
          },
    })
}

$(document).ready(function() {
    $('#stat_date_range_picker').daterangepicker({
        opens: 'left',
    });
    $('#stat_date_range_picker').on('change', function() {
        fill_plots();
    });
    fill_plots();
});