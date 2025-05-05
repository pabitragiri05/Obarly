document.addEventListener("DOMContentLoaded", function () {
    const loginSignupContainer = document.getElementById("loginSignupContainer");
    const locationContainer = document.getElementById("locationContainer");
    const moreButton = document.getElementById("more-button");
    const closePopupButtons = document.querySelectorAll("#closePopup");
    const toggleSignup = document.getElementById("toggleSignup");
    const toggleLogin = document.getElementById("toggleLogin");
    const toggleAdminLogin = document.getElementById("toggleAdminLogin"); // Admin login toggle
    const loginForm = document.getElementById("loginForm");
    const signupForm = document.getElementById("signupForm");
    const adminLoginForm = document.getElementById("adminLoginForm");
    
    // Show login/signup popup
    moreButton.addEventListener("click", function () {
        loginSignupContainer.classList.remove("hidden");
    });
    
    // Close popups
    closePopupButtons.forEach(button => {
        button.addEventListener("click", function () {
            loginSignupContainer.classList.add("hidden");
            locationContainer.classList.add("hidden");
        });
    });
    
    // Toggle between login and signup forms
    toggleSignup.addEventListener("click", function (e) {
        e.preventDefault();
        loginForm.classList.add("hidden");
        adminLoginForm.classList.add("hidden");
        signupForm.classList.remove("hidden");
    });
    
    toggleLogin.addEventListener("click", function (e) {
        e.preventDefault();
        signupForm.classList.add("hidden");
        adminLoginForm.classList.add("hidden");
        loginForm.classList.remove("hidden");
    });
    
    // Toggle between login and admin login forms
    toggleAdminLogin.addEventListener("click", function (e) {
        e.preventDefault();
        loginForm.classList.add("hidden");
        signupForm.classList.add("hidden");
        adminLoginForm.classList.remove("hidden");
    });
    
    // Handle admin login form submission
    adminLoginForm.addEventListener("submit", function (e) {
        e.preventDefault();
        const formData = new FormData(adminLoginForm);
        
        fetch('/admin-login', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.redirected) {
                window.location.href = response.url;
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
    
    // Show location popup
    document.querySelector("nav a:first-child").addEventListener("click", function () {
        locationContainer.classList.remove("hidden");
    });
});
