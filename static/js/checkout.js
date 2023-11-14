
// Step 2: Create an instance of Elements with the clientSecret
var elements = stripe.elements({
    clientSecret: clientSecret
});

// Step 3: Create the card element
var cardElement = elements.create('payment');

// Step 4: Mount the element to the div
cardElement.mount('#payment-element');

// Step 5: Handle form submission
var form = document.getElementById('payment-form');

form.addEventListener('submit', function (event) {
    event.preventDefault();

    // Modify the button to show spinner and change text
    const btn = form.querySelector('button[type="submit"]');
    btn.querySelector('.spinner-border').style.display = 'inline-block';
    btn.querySelector('.btn-text').textContent = 'Processing Order...';
    btn.disabled = true;  // Disable the button to prevent double-clicks

    stripe.createPaymentMethod('card', cardElement).then(function (result) {
        if (result.error) {
            console.error(result.error.message);

            // Revert the button to its original state
            revertButtonState(btn);
        } else {
            // Add the payment method ID to the form as a hidden field
            var hiddenInput = document.createElement('input');
            hiddenInput.setAttribute('type', 'hidden');
            hiddenInput.setAttribute('name', 'payment_method');
            hiddenInput.setAttribute('value', result.paymentMethod.id);
            form.appendChild(hiddenInput);

            // Submit the form to your server with the payment method ID
            fetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                headers: {
                    'X-CSRFToken': '{{ csrf_token }}'
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.location.href = data.redirect_url;
                    } else {
                        console.error('Order placement failed:', data.error);
                        revertButtonState(btn);
                    }
                })
                .catch(error => {
                    console.error('Error submitting the form:', error);
                    revertButtonState(btn);
                });
        }
    });
});

function revertButtonState(btn) {
    btn.querySelector('.spinner-border').style.display = 'none';
    btn.querySelector('.btn-text').textContent = 'Place Order';
    btn.disabled = false;
}

document.addEventListener('DOMContentLoaded', function () {
    const useDifferentShippingAddressCheckbox = document.querySelector('#id_use_different_shipping_address');
    const shippingFieldContainer = document.querySelector('.shipping-field');
    const shippingInputs = document.querySelectorAll('.shipping-field input');

    function toggleShippingFields() {
        if (useDifferentShippingAddressCheckbox.checked) {
            shippingFieldContainer.style.display = 'block';
        } else {
            shippingFieldContainer.style.display = 'none';
        }

        // Set or unset the required attribute based on checkbox state
        shippingInputs.forEach(input => {
            if (useDifferentShippingAddressCheckbox.checked || input.id === 'id_shipping_address_line2') {
                input.required = true;
            } else {
                input.required = false;
            }
        });
    }

    useDifferentShippingAddressCheckbox.addEventListener('change', toggleShippingFields);
    toggleShippingFields();  // Call once to set the initial state

    // Copy billing values to shipping when form is submitted
    document.getElementById('payment-form').addEventListener('submit', function (e) {
        if (!useDifferentShippingAddressCheckbox.checked) {
            document.getElementById('id_shipping_first_name').value = document.getElementById('id_first_name').value;
            document.getElementById('id_shipping_last_name').value = document.getElementById('id_last_name').value;
            document.getElementById('id_shipping_address_line1').value = document.getElementById('id_billing_address_line1').value;
            document.getElementById('id_shipping_address_line2').value = document.getElementById('id_billing_address_line2').value || "";  // Default to empty string if no value
            document.getElementById('id_shipping_city').value = document.getElementById('id_billing_city').value;
            document.getElementById('id_shipping_state').value = document.getElementById('id_billing_state').value;
            document.getElementById('id_shipping_postal_code').value = document.getElementById('id_billing_postal_code').value;
        }
    });
});


function moveToPaymentStep() {
    var addressDetails = document.getElementById('addressDetails');
    var paymentDetails = document.getElementById('paymentDetails');

    if (addressDetails) {
        addressDetails.style.display = 'none';
    }
    if (paymentDetails) {
        paymentDetails.style.display = 'block';
    }
}



 