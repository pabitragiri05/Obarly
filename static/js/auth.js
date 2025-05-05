document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');
    const toggleSignup = document.getElementById('toggleSignup');
    const toggleLogin = document.getElementById('toggleLogin');
    const closePopup = document.getElementById('closePopup');
    const loginSignupContainer = document.getElementById('loginSignupContainer');

    // Show/hide login signup container
    document.querySelector('a[href="#login"]').addEventListener('click', function(e) {
        e.preventDefault();
        loginSignupContainer.classList.remove('hidden');
        showLoginForm();
    });

    // Close popup when clicking the close button
    closePopup.addEventListener('click', function() {
        loginSignupContainer.classList.add('hidden');
    });

    // Close popup when clicking outside the form
    loginSignupContainer.addEventListener('click', function(e) {
        if (e.target === loginSignupContainer) {
            loginSignupContainer.classList.add('hidden');
        }
    });

    // Toggle between login and signup forms
    toggleSignup.addEventListener('click', function(e) {
        e.preventDefault();
        showSignupForm();
    });

    toggleLogin.addEventListener('click', function(e) {
        e.preventDefault();
        showLoginForm();
    });

    function showLoginForm() {
        loginForm.classList.remove('hidden');
        signupForm.classList.add('hidden');
    }

    function showSignupForm() {
        loginForm.classList.add('hidden');
        signupForm.classList.remove('hidden');
    }
}); 