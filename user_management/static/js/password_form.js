document.getElementById("forgot-password-btn").addEventListener("click", function() {

    var forgotPasswordForm = document.getElementById("forgot-password-form");
    var loginForm = document.getElementById("login-form");
    var forgotPasswordBtn = document.getElementById("forgot-password-btn")
    
    if (forgotPasswordForm.style.display === "none") {
        loginForm.style.display = "none";  
        forgotPasswordForm.style.display = "block";
        forgotPasswordBtn.innerText = "Geri";  
    } else {
        loginForm.style.display = "block";  
        forgotPasswordForm.style.display = "none"; 
        forgotPasswordBtn.innerText = "Şifremi Unuttum";
    }
});