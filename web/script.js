const state = {
  apiUrl: localStorage.getItem("apiUrl") || "http://127.0.0.1:8000",
  token: localStorage.getItem("token") || "",
};

const el = (id) => document.getElementById(id);

const log = (msg) => {
  const box = el("messages");
  const now = new Date().toLocaleTimeString();
  box.textContent = `[${now}] ${msg}\n` + box.textContent;
};

const authHeaders = () =>
  state.token
    ? {
        Authorization: `Bearer ${state.token}`,
      }
    : {};

const parseNumberOrNull = (v) => {
  if (v === "" || v === null || v === undefined) return null;
  const n = Number(v);
  return Number.isNaN(n) ? null : n;
};

const apiFetch = async (path, options = {}) => {
  const res = await fetch(`${state.apiUrl}${path}`, {
    ...options,
    headers: {
      ...(options.headers || {}),
      ...authHeaders(),
    },
  });
  if (!res.ok) {
    let text = "";
    try {
      text = await res.text();
    } catch (_) {}
    throw new Error(`HTTP ${res.status} - ${text}`);
  }
  if (res.status === 204) return null;
  return res.json();
};

const renderToken = () => {
  el("tokenPreview").textContent = state.token ? state.token.slice(0, 24) + "..." : "No logueado";
  el("dashboard-card").classList.toggle("hidden", !state.token);
  el("entities-card").classList.toggle("hidden", !state.token);
};

const saveApiConfig = () => {
  state.apiUrl = el("apiUrl").value.trim();
  localStorage.setItem("apiUrl", state.apiUrl);
  log(`Base URL guardada: ${state.apiUrl}`);
};

const register = async (ev) => {
  ev.preventDefault();
  const fd = new FormData(ev.target);
  const payload = Object.fromEntries(fd.entries());
  await apiFetch("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  log("Usuario registrado.");
  ev.target.reset();
};

const login = async (ev) => {
  ev.preventDefault();
  const fd = new FormData(ev.target);
  const formBody = new URLSearchParams(fd).toString();
  const res = await fetch(`${state.apiUrl}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formBody,
  });
  if (!res.ok) throw new Error(`Login fallo (${res.status})`);
  const data = await res.json();
  state.token = data.access_token;
  localStorage.setItem("token", state.token);
  renderToken();
  log("Sesion iniciada.");
  await refreshAll();
};

const logout = () => {
  state.token = "";
  localStorage.removeItem("token");
  renderToken();
  log("Sesion cerrada.");
};

const tableFrom = (items, fields, removeCb) => {
  if (!items.length) return "<p>Sin registros.</p>";
  const headers = fields.map((f) => `<th>${f}</th>`).join("");
  const rows = items
    .map((it) => {
      const cols = fields.map((f) => `<td>${it[f] ?? ""}</td>`).join("");
      return `<tr>${cols}<td><button data-id="${it.id}" class="del-btn">Eliminar</button></td></tr>`;
    })
    .join("");
  setTimeout(() => {
    document.querySelectorAll(".del-btn").forEach((btn) => {
      btn.onclick = () => removeCb(Number(btn.dataset.id));
    });
  }, 0);
  return `<table class="list-table"><thead><tr>${headers}<th>Accion</th></tr></thead><tbody>${rows}</tbody></table>`;
};

const refreshDashboard = async () => {
  const d = await apiFetch("/dashboard");
  el("totalExpenses").textContent = d.total_expenses;
  el("totalDebts").textContent = d.total_debts;
  el("totalIncomes").textContent = d.total_incomes;
  el("balance").textContent = d.balance;
};

const refreshExpenses = async () => {
  const items = await apiFetch("/expenses");
  el("expensesList").innerHTML = tableFrom(
    items,
    ["id", "title", "amount", "due_date", "assigned_to_user_id", "paid_by_user_id"],
    async (id) => {
      await apiFetch(`/expenses/${id}`, { method: "DELETE" });
      log(`Gasto ${id} eliminado.`);
      await refreshExpenses();
      await refreshDashboard();
    }
  );
};

const refreshDebts = async () => {
  const items = await apiFetch("/debts");
  el("debtsList").innerHTML = tableFrom(
    items,
    ["id", "creditor", "amount", "status", "due_date", "assigned_to_user_id", "paid_by_user_id"],
    async (id) => {
      await apiFetch(`/debts/${id}`, { method: "DELETE" });
      log(`Deuda ${id} eliminada.`);
      await refreshDebts();
      await refreshDashboard();
    }
  );
};

const refreshIncomes = async () => {
  const items = await apiFetch("/incomes");
  el("incomesList").innerHTML = tableFrom(
    items,
    ["id", "source", "amount", "income_date", "assigned_to_user_id"],
    async (id) => {
      await apiFetch(`/incomes/${id}`, { method: "DELETE" });
      log(`Ingreso ${id} eliminado.`);
      await refreshIncomes();
      await refreshDashboard();
    }
  );
};

const refreshEvents = async () => {
  const items = await apiFetch("/events");
  el("eventsList").innerHTML = tableFrom(
    items,
    ["id", "title", "event_datetime", "location", "assigned_to_user_id"],
    async (id) => {
      await apiFetch(`/events/${id}`, { method: "DELETE" });
      log(`Evento ${id} eliminado.`);
      await refreshEvents();
    }
  );
};

const refreshAttachments = async () => {
  const items = await apiFetch("/attachments");
  if (!items.length) {
    el("attachmentsList").innerHTML = "<p>Sin adjuntos.</p>";
    return;
  }
  el("attachmentsList").innerHTML = `<table class="list-table">
    <thead><tr><th>id</th><th>tipo</th><th>archivo</th><th>ruta</th><th>gasto</th><th>deuda</th><th>ingreso</th></tr></thead>
    <tbody>
      ${items
        .map(
          (it) => `<tr>
          <td>${it.id}</td>
          <td>${it.kind}</td>
          <td>${it.original_filename}</td>
          <td>${it.saved_path}</td>
          <td>${it.expense_id ?? ""}</td>
          <td>${it.debt_id ?? ""}</td>
          <td>${it.income_id ?? ""}</td>
        </tr>`
        )
        .join("")}
    </tbody>
  </table>`;
};

const createEntitySubmit = (formId, endpoint, mapper, refreshFn) => {
  el(formId).addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData(ev.target);
    const payload = mapper(fd);
    await apiFetch(`/${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    log(`${endpoint.slice(0, -1)} creado.`);
    ev.target.reset();
    await refreshFn();
    if (["expenses", "debts", "incomes"].includes(endpoint)) await refreshDashboard();
  });
};

const refreshAll = async () => {
  if (!state.token) return;
  await Promise.all([refreshDashboard(), refreshExpenses(), refreshDebts(), refreshIncomes(), refreshEvents(), refreshAttachments()]);
};

const setupTabs = () => {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.onclick = () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      el(`tab-${btn.dataset.tab}`).classList.add("active");
    };
  });
};

const init = () => {
  el("apiUrl").value = state.apiUrl;
  renderToken();
  setupTabs();

  el("saveApiUrl").onclick = saveApiConfig;
  el("registerForm").addEventListener("submit", (ev) => register(ev).catch((e) => log(e.message)));
  el("loginForm").addEventListener("submit", (ev) => login(ev).catch((e) => log(e.message)));
  el("logoutBtn").onclick = logout;
  el("refreshDashboard").onclick = () => refreshDashboard().catch((e) => log(e.message));
  el("refreshAttachments").onclick = () => refreshAttachments().catch((e) => log(e.message));

  createEntitySubmit(
    "expenseForm",
    "expenses",
    (fd) => ({
      title: String(fd.get("title") || ""),
      amount: Number(fd.get("amount")),
      due_date: String(fd.get("due_date") || "") || null,
      description: String(fd.get("description") || "") || null,
      assigned_to_user_id: parseNumberOrNull(fd.get("assigned_to_user_id")),
      paid_by_user_id: parseNumberOrNull(fd.get("paid_by_user_id")),
    }),
    refreshExpenses
  );

  createEntitySubmit(
    "debtForm",
    "debts",
    (fd) => ({
      creditor: String(fd.get("creditor") || ""),
      amount: Number(fd.get("amount")),
      due_date: String(fd.get("due_date") || "") || null,
      description: String(fd.get("description") || "") || null,
      status: String(fd.get("status") || "pending"),
      assigned_to_user_id: parseNumberOrNull(fd.get("assigned_to_user_id")),
      paid_by_user_id: parseNumberOrNull(fd.get("paid_by_user_id")),
    }),
    refreshDebts
  );

  createEntitySubmit(
    "incomeForm",
    "incomes",
    (fd) => ({
      source: String(fd.get("source") || ""),
      amount: Number(fd.get("amount")),
      income_date: String(fd.get("income_date") || "") || null,
      description: String(fd.get("description") || "") || null,
      assigned_to_user_id: parseNumberOrNull(fd.get("assigned_to_user_id")),
    }),
    refreshIncomes
  );

  createEntitySubmit(
    "eventForm",
    "events",
    (fd) => ({
      title: String(fd.get("title") || ""),
      event_datetime: String(fd.get("event_datetime") || ""),
      location: String(fd.get("location") || "") || null,
      description: String(fd.get("description") || "") || null,
      assigned_to_user_id: parseNumberOrNull(fd.get("assigned_to_user_id")),
    }),
    refreshEvents
  );

  el("attachmentForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData(ev.target);
    const entity = String(fd.get("entity"));
    const entityId = Number(fd.get("entityId"));
    const kind = String(fd.get("kind") || "ticket");
    const file = fd.get("file");

    const form = new FormData();
    form.append("file", file);
    await apiFetch(`/${entity}/${entityId}/attachments?kind=${encodeURIComponent(kind)}`, {
      method: "POST",
      body: form,
    });
    log("Adjunto subido.");
    ev.target.reset();
    await refreshAttachments();
  });

  refreshAll().catch((e) => log(e.message));
};

init();
