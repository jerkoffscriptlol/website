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
    let row = document.createElement("tr");
    row.innerHTML = `
      <td>${entry.username}</td>
      <td>${entry.displayname}</td>
      <td>${entry.game}</td>
      <td>${entry.ip || "N/A"}</td>
      <td>
        <button onclick="deleteLog('${entry.userid}')">Delete</button>
        <button onclick="sendToDiscord('${entry.userid}')">Send</button>
      </td>
    `;
    table.appendChild(row);
  });
}

async function deleteLog(userid) {
  await fetch(`/logs/${userid}`, {
    method: "DELETE",
    headers: { "Authorization": sessionStorage.getItem("auth") }
  });
  loadLogs();
}

async function sendToDiscord(userid) {
  await fetch(`/send_log/${userid}`, {
    method: "POST",
    headers: { "Authorization": sessionStorage.getItem("auth") }
  });
}
