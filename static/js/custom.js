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

$(document).ready(function() {
    $('.card-clickable').on('click', function() {
        window.location.href = $(this).data('url');
    });
});

$(document).ready(function(){
    // Set a timeout for all messages with class 'alert' (bootstrap's class)
    $(".alert").delay(3000).slideUp(300, function(){
        $(this).alert('close');
    });
});