const API_BASE = `http://${window.location.hostname || "127.0.0.1"}:8000`;

function getAuth() {
  return {
    token: localStorage.getItem("token"),
    username: localStorage.getItem("username"),
    name: localStorage.getItem("name"),
    role: localStorage.getItem("role"),
  };
}

function saveAuth(data) {
  localStorage.setItem("token", data.access_token);
  localStorage.setItem("username", data.username);
  localStorage.setItem("name", data.name);
  localStorage.setItem("role", data.role);
}

function clearAuth() {
  localStorage.removeItem("token");
  localStorage.removeItem("username");
  localStorage.removeItem("name");
  localStorage.removeItem("role");
}

function showAlert(message, type = "success") {
  const box = document.getElementById("alertBox");
  if (!box) return;
  box.textContent = message;
  box.className = `alert alert-${type}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

async function apiRequest(path, options = {}) {
  const { token } = getAuth();
  const headers = { ...(options.headers || {}) };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  } catch {
    throw new Error(`Unable to connect to the backend service at ${API_BASE}. Please verify that the server is running.`);
  }

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data.detail || `Request failed with status ${res.status}.`);
  }
  return data;
}

function renderNavbar() {
  const nav = document.getElementById("navLinks");
  const { token, username, role } = getAuth();

  if (!token) {
    nav.innerHTML = `
      <a href="index.html" class="btn btn-ghost">Home</a>
      <a href="index.html#authSection" class="btn btn-primary">Login / Register</a>
    `;
    return;
  }

  nav.innerHTML = `
    <span class="nav-user">Signed in as <strong>${escapeHtml(username)}</strong> (${escapeHtml(role)})</span>
    <a href="index.html" class="btn btn-ghost">Pets & Support</a>
    <a href="dashboard.html" class="btn btn-primary">Dashboard</a>
    <button type="button" id="logoutBtn" class="btn btn-danger">Logout</button>
  `;

  document.getElementById("logoutBtn").addEventListener("click", () => {
    clearAuth();
    window.location.href = "index.html";
  });
}

// Public Catalog and Authentication View (index.html)

async function loadPublicPets() {
  const container = document.getElementById("petsContainer");
  const { role } = getAuth();
  const pets = await apiRequest("/pets");

  if (!pets.length) {
    container.innerHTML = `<div class="card">No pets are currently listed for adoption.</div>`;
    return;
  }

  container.innerHTML = pets
    .map((pet) => {
      const imgSrc = pet.image_url || "https://placehold.co/400x240?text=Pet";
      const adoptBtn =
        role === "adopter"
          ? `<button class="btn btn-secondary" onclick="requestAdoption(${pet.id})">Request Adoption</button>`
          : "";

      return `
        <div class="card pet-card">
          <img src="${escapeHtml(imgSrc)}" alt="${escapeHtml(pet.pet_name)}" />
          <h3>${escapeHtml(pet.pet_name)}</h3>
          <div class="pet-meta">Adoption Fee: $${Number(pet.adoption_fee).toFixed(2)}</div>
          ${adoptBtn}
        </div>
      `;
    })
    .join("");
}

window.requestAdoption = async function (petId) {
  try {
    const res = await apiRequest("/adoptions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pet_id: petId }),
    });
    showAlert(res.message || "Adoption request submitted successfully.");
  } catch (err) {
    showAlert(err.message, "error");
  }
};

async function loadSupportTickets() {
  const container = document.getElementById("supportContainer");
  const tickets = await apiRequest("/support");

  if (!tickets.length) {
    container.innerHTML = `<div class="list-item">No support announcements are currently available.</div>`;
    return;
  }

  container.innerHTML = tickets
    .map(
      (t) => `
      <div class="list-item">
        <div>
          <span class="badge">${escapeHtml(t.ticket_id)}</span>
          <p style="margin-top:0.35rem;">${escapeHtml(t.msg)}</p>
        </div>
      </div>
    `
    )
    .join("");
}

function setupAuthForms() {
  const { token } = getAuth();
  const authSection = document.getElementById("authSection");
  if (token && authSection) {
    authSection.classList.add("hidden");
  }

  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        const body = new URLSearchParams({
          username: document.getElementById("loginUsername").value.trim(),
          password: document.getElementById("loginPassword").value,
        });
        const data = await apiRequest("/login", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body,
        });
        saveAuth(data);
        window.location.href = "dashboard.html";
      } catch (err) {
        showAlert(err.message, "error");
      }
    });
  }

  const registerForm = document.getElementById("registerForm");
  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        const payload = {
          name: document.getElementById("regName").value.trim(),
          username: document.getElementById("regUsername").value.trim(),
          phone: document.getElementById("regPhone").value.trim() || null,
          password: document.getElementById("regPassword").value,
        };
        const res = await apiRequest("/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        registerForm.reset();
        showAlert(res.message || "Registration completed. Please sign in to continue.");
      } catch (err) {
        showAlert(err.message, "error");
      }
    });
  }
}

// Role-Based Dashboard View (dashboard.html)

async function loadAdminPets() {
  const list = document.getElementById("adminPetsList");
  const pets = await apiRequest("/pets");

  if (!pets.length) {
    list.innerHTML = `<div class="list-item">No pet records found in the catalog.</div>`;
    return;
  }

  list.innerHTML = pets
    .map(
      (p) => `
      <div class="list-item">
        <div>
          <strong>${escapeHtml(p.pet_name)}</strong> — $${Number(p.adoption_fee).toFixed(2)}
        </div>
        <div class="btn-row">
          <button class="btn btn-ghost" onclick='startEditPet(${JSON.stringify(p)})'>Edit</button>
          <button class="btn btn-danger" onclick="deletePet(${p.id})">Delete</button>
        </div>
      </div>
    `
    )
    .join("");
}

window.startEditPet = function (pet) {
  document.getElementById("petFormTitle").textContent = `Edit Pet #${pet.id}`;
  document.getElementById("editPetId").value = pet.id;
  document.getElementById("petName").value = pet.pet_name;
  document.getElementById("petImage").value = pet.image_url || "";
  document.getElementById("petFee").value = pet.adoption_fee;
  document.getElementById("cancelEditPetBtn").classList.remove("hidden");
};

window.deletePet = async function (petId) {
  try {
    const res = await apiRequest(`/pets/${petId}`, { method: "DELETE" });
    showAlert(res.message);
    await loadAdminPets();
  } catch (err) {
    showAlert(err.message, "error");
  }
};

window.updateAdoptionStatus = async function (requestId, status) {
  try {
    const res = await apiRequest(`/adoptions/${requestId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    showAlert(res.message);
    await loadAdoptions();
  } catch (err) {
    showAlert(err.message, "error");
  }
};

async function loadAdoptions() {
  const container = document.getElementById("adoptionsContainer");
  const { role } = getAuth();
  const items = await apiRequest("/adoptions");

  if (!items.length) {
    container.innerHTML = `<div class="list-item">No adoption requests found.</div>`;
    return;
  }

  container.innerHTML = items
    .map((req) => {
      const petName = req.pet ? req.pet.pet_name : "Unknown Pet";
      const fee = req.pet ? `$${Number(req.pet.adoption_fee).toFixed(2)}` : "-";
      const adopterName = req.adopter ? `${req.adopter.name} (@${req.adopter.username})` : "Unknown User";

      const adminControls =
        role === "admin"
          ? `
            <div class="btn-row">
              <button class="btn btn-secondary" onclick="updateAdoptionStatus(${req.id}, 'approved')">Approve</button>
              <button class="btn btn-danger" onclick="updateAdoptionStatus(${req.id}, 'rejected')">Reject</button>
            </div>
          `
          : "";

      return `
        <div class="list-item">
          <div>
            <div><strong>Request #${req.id}</strong> — <span class="badge">${escapeHtml(req.status)}</span></div>
            <div>Pet: <strong>${escapeHtml(petName)}</strong> (Fee: ${fee})</div>
            <div>Adopter: ${escapeHtml(adopterName)}</div>
          </div>
          ${adminControls}
        </div>
      `;
    })
    .join("");
}

function setupDashboardForms() {
  const petForm = document.getElementById("petForm");
  const cancelBtn = document.getElementById("cancelEditPetBtn");

  cancelBtn.addEventListener("click", () => {
    petForm.reset();
    document.getElementById("editPetId").value = "";
    document.getElementById("petFormTitle").textContent = "Add New Pet";
    cancelBtn.classList.add("hidden");
  });

  petForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("editPetId").value;
    const payload = {
      pet_name: document.getElementById("petName").value.trim(),
      image_url: document.getElementById("petImage").value.trim() || null,
      adoption_fee: parseFloat(document.getElementById("petFee").value),
    };

    try {
      if (id) {
        const res = await apiRequest(`/pets/${id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        showAlert(res.message);
      } else {
        const res = await apiRequest("/pets", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        showAlert(res.message);
      }
      cancelBtn.click();
      await loadAdminPets();
    } catch (err) {
      showAlert(err.message, "error");
    }
  });

  document.getElementById("createSupportForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const res = await apiRequest("/support", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticket_id: document.getElementById("supportTicketId").value.trim(),
          msg: document.getElementById("supportMsg").value.trim(),
        }),
      });
      e.target.reset();
      showAlert(res.message);
    } catch (err) {
      showAlert(err.message, "error");
    }
  });

  document.getElementById("updateSupportForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const ticketId = encodeURIComponent(document.getElementById("updateTicketId").value.trim());
    try {
      const res = await apiRequest(`/support/${ticketId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          msg: document.getElementById("updateSupportMsg").value.trim(),
        }),
      });
      e.target.reset();
      showAlert(res.message);
    } catch (err) {
      showAlert(err.message, "error");
    }
  });
}

// Application Initialization

document.addEventListener("DOMContentLoaded", async () => {
  renderNavbar();
  const page = document.body.dataset.page;

  try {
    if (page === "index") {
      setupAuthForms();
      await Promise.all([loadPublicPets(), loadSupportTickets()]);
    } else if (page === "dashboard") {
      const { token, role, username } = getAuth();
      if (!token) {
        window.location.href = "index.html";
        return;
      }

      document.getElementById("dashTitle").textContent = `${role.toUpperCase()} Dashboard`;
      document.getElementById("dashSubtitle").textContent = `Authenticated as ${username}`;

      setupDashboardForms();
      await loadAdoptions();

      if (role === "admin") {
        document.getElementById("adminPetsSection").classList.remove("hidden");
        document.getElementById("adminSupportSection").classList.remove("hidden");
        await loadAdminPets();
      }
    }
  } catch (err) {
    showAlert(err.message, "error");
  }
});