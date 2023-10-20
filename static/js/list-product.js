$(document).ready(function() {
    // Function to handle the change event for autocomplete
    function handleAutocompleteChange(event, ui) {
        var warningElementId = $(this).attr('id') + '-warning';
        if (!ui.item) {
            // If the current value doesn't match any suggestion, clear the input
            $(this).val('');
            // Show the warning message above the input
            $('#' + warningElementId).show();
        } else {
            // Hide the warning if the input is valid
            $('#' + warningElementId).hide();
        }
    }

    // Autocomplete functionality for brand
    $("#brand").autocomplete({
        source: '/search_brands/',
        minLength: 1,
        select: function(event, ui) {
            // Hide the warning when a valid option is selected
            $('#brand-warning').hide();
        },
        change: handleAutocompleteChange
    });

    // Autocomplete functionality for category
    $("#category").autocomplete({
        source: '/search_categories/',
        minLength: 1,
        select: function(event, ui) {
            // Hide the warning when a valid option is selected
            $('#category-warning').hide();
        },
        change: handleAutocompleteChange
    });

    // Click functionality for clickable cards
    $('.card-clickable').on('click', function() {
        window.location.href = $(this).data('url');
    });

    // Set a timeout for all alert messages
    $(".alert").delay(3000).slideUp(300, function(){
        $(this).alert('close');
    });

    // Before submitting the form
    $("#productForm").on('submit', function(e) {
        if (!$("#brand").val()) {
            $("#brand-warning").show();
            e.preventDefault();
        }
        if (!$("#category").val()) {
            $("#category-warning").show();
            e.preventDefault();
        }
    });
});
