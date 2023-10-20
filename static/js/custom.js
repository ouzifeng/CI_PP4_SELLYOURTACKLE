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



// Live search dropdown functionality
const searchInput = document.getElementById('search_text');
const resultsDropdown = document.createElement('div');
resultsDropdown.classList.add('search-dropdown');
searchInput.parentElement.appendChild(resultsDropdown);

searchInput.addEventListener('keyup', function() {
    if (this.value.length > 2) {
        fetch(`/search/?search_text=${this.value}`)
        .then(response => response.json())
        .then(data => {
            resultsDropdown.innerHTML = '';  // Clear previous results
            if (data.length > 0) {
                data.forEach(product => {
                    let item = document.createElement('a');
                    item.href = `/product/${product.slug}`;
                    item.innerText = product.name;
                    resultsDropdown.appendChild(item);
                });
            } else {
                // If there are no results, display a message
                resultsDropdown.innerHTML = `
                    <span class="no-results">
                        <a href="#">Sorry, no matches for this item. Click to browse all products</a>
                    </span>
                `;
            }
        });
    } else {
        resultsDropdown.innerHTML = '';  // Clear previous results
    }
});


document.getElementById('signupForm').addEventListener('submit', function (e) {
    var signupButton = document.getElementById('signupButton');
    var buttonText = document.getElementById('buttonText');
    var spinner = document.getElementById('spinner');

    // Prevent multiple form submissions
    if (signupButton.disabled) {
        e.preventDefault();
    } else {
        // Disable the button
        signupButton.disabled = true;

        // Hide the button text
        buttonText.style.display = 'none';

        // Show the spinner
        spinner.style.display = 'inline-block';
    }
});
