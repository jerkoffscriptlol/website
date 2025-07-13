async function login() {
  const pwd = document.getElementById("password").value;
  const res = await fetch("/auth", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password: pwd })
  });
  if (res.ok) {
    sessionStorage.setItem("auth", pwd);
    document.getElementById("login").classList.add("hidden");
    document.getElementById("dashboard").classList.remove("hidden");
    loadLogs();
  } else {
    document.getElementById("error").innerText = "Incorrect password.";
  }
}

async function loadLogs() {
  const res = await fetch("/logs", {
    headers: { "Authorization": sessionStorage.getItem("auth") }
  });
  const data = await res.json();
  const table = document.querySelector("#logTable tbody");
  table.innerHTML = "";
  data.forEach(entry => {
    let row = `<tr>
      <td>${entry.username}</td>
      <td>${entry.displayname}</td>
      <td>${entry.game}</td>
      <td>${entry.ip || "N/A"}</td>
    </tr>`;
    table.innerHTML += row;
  });
}
