// This JS file is for signup button fuctionality
/*jshint esversion: 6 */

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
