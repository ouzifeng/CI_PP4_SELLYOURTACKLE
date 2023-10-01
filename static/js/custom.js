$(document).ready(function() {
    $("#brand").autocomplete({
        source: '/search_brands/',
        minLength: 1, // trigger autocomplete after 1 character
        select: function(event, ui) {
            // optionally do something after the user selects an option
        }
    });

    $("#category").autocomplete({
        source: '/search_categories/',
        minLength: 1,
        select: function(event, ui) {
            // optionally do something after the user selects an option
        }
    });
});