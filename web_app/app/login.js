import "./login_style.css";

const flaskUrl = import.meta.env.VITE_FLASK_URL;

document.getElementById("login-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  fetch(flaskUrl + "login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
    credentials: "include",
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.message === "Logged in successfully") {
        console.log(data);
        window.location.href = "/demo.html";
      } else {
        alert("Login failed: " + data.error);
      }
    })
    .catch((error) => console.error("Error:", error));
});
