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
                        <a href="/shop">Sorry, no matches for this item. Click to browse all products</a>
                    </span>
                `;
            }
        });
    } else {
        resultsDropdown.innerHTML = '';  // Clear previous results
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
