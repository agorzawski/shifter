    $(document).ready(function() {

        $('#remote .typeahead').typeahead(null, {
                highlight: true,
    minLength: 2,
    limit: Infinity,
            name: 'best-pictures',
            display: 'value',
            source: function (query, processSync, processAsync) {
                return $.get($('#remote').data('source-url'), { search: query }, function (data) {
                    return processAsync(data);
                });
            }
        }).bind('typeahead:selected', function(obj, selected, name) {
            location.href = selected.url
        }).off('blur');

    });