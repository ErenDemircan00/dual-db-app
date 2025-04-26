const token = new URLSearchParams(window.location.search).get("token");

function submitForm(e) {
    e.preventDefault();
    const password = document.getElementById("new_password").value;

    fetch(`/reset-password?token=${token}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ new_password: password })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
        if (data.message.includes("başarıyla")) {
            window.location.href = "/login";
        }
    })
    .catch(err => {
        console.error("Hata:", err);
        alert("Bir hata oluştu. Lütfen tekrar deneyin.");
    });
}
