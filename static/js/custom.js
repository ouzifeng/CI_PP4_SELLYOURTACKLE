$(document).ready(function() {
    // Autocomplete functionality for brand and category
    $("#brand").autocomplete({
        source: '/search_brands/',
        minLength: 1,
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

    // Click functionality for clickable cards
    $('.card-clickable').on('click', function() {
        window.location.href = $(this).data('url');
    });

    // Set a timeout for all alert messages
    $(".alert").delay(3000).slideUp(300, function(){
        $(this).alert('close');
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
            resultsDropdown.innerHTML = '';
            data.forEach(product => {
                let item = document.createElement('a');
                item.href = `/product/${product.slug}`;
                item.innerText = product.name;
                resultsDropdown.appendChild(item);
            });
        });
    } else {
        resultsDropdown.innerHTML = '';
    }
});
