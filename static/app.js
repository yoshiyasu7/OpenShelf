(function () {
  const rawApiBase =
    document.querySelector('meta[name="api-base"]')?.getAttribute("content") || "/api/v1";
  const API_BASE = rawApiBase.replace(/\/$/, "");

  const K_ACCESS = "openshelf:access";
  const K_REFRESH = "openshelf:refresh";
  const K_USER = "openshelf:user";
  const K_LOANS = "openshelf:loans";

  const el = (id) => document.getElementById(id);
  const msg = (text, isOk) => {
    const m = el("msg");
    if (!text) {
      m.hidden = true;
      m.textContent = "";
      m.classList.remove("ok");
      return;
    }
    m.hidden = false;
    m.textContent = text;
    m.classList.toggle("ok", !!isOk);
  };

  function apiRootUrl() {
    if (API_BASE.startsWith("http://") || API_BASE.startsWith("https://")) {
      try {
        return new URL(API_BASE).origin;
      } catch {
        return "";
      }
    }
    return window.location.origin;
  }

  /** Сообщения для `error.code` из бэкенда (src/infrastructure/logging/middleware exception_handler). */
  const API_ERROR_RU = {
    LOAN_LIMIT_EXCEEDED:
      "Можно держать на руках только ограниченное число книг (5). Сдайте одну, чтобы взять другую.",
    NO_AVAILABLE_INSTANCES: "Свободных экземпляров нет: все в выдаче (на руках у читателей).",
    ALREADY_BORROWING_BOOK:
      "У вас уже есть на руках экземпляр этой книги. Сдайте его, прежде чем брать снова.",
    CONCURRENCY_CONFLICT: "Книгу только что взял другой читатель. Попробуйте ещё раз.",
    LOAN_OVERDUE: "Есть книги, не сданные в срок, — новая выдача пока невозможна.",
    LOAN_NOT_FOUND: "Такой выдачи в системе нет.",
    LOAN_ALREADY_RETURNED: "Эта книга уже сдана.",
  };

  /** Сообщения `detail` из HTTPException (FastAPI), оригинал на англ. */
  const API_HTTP_DETAIL_RU = {
    "Invalid credentials": "Неверный логин или пароль. Проверьте данные и попробуйте снова.",
    "Invalid refresh token": "Сессия устарела. Войдите снова.",
  };

  /**
   * Бэкенд отдаёт { error: { code, message } }, не FastAPI-формат { detail: ... }.
   * Иначе в UI остаётся «Unprocessable Content».
   */
  function messageFromErrorBody(j) {
    if (!j) return "";
    if (j.error) {
      const { code, message } = j.error;
      if (code && API_ERROR_RU[code]) {
        return API_ERROR_RU[code];
      }
      if (message) {
        return String(message);
      }
      if (j.error.code === "VALIDATION_ERROR" && j.error.details) {
        const first = Array.isArray(j.error.details) ? j.error.details[0] : null;
        if (first && (first.msg || first.message)) {
          return String(first.msg || first.message);
        }
        return "Некорректные данные";
      }
    }
    if (Array.isArray(j.detail)) {
      return j.detail
        .map((d) => (typeof d === "string" ? d : d?.msg != null ? d.msg : String(d)))
        .join(", ");
    }
    if (j.detail != null) {
      const s = String(j.detail);
      return API_HTTP_DETAIL_RU[s] || s;
    }
    return "";
  }

  function getUser() {
    const raw = localStorage.getItem(K_USER);
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  function setSession(access, refresh, user) {
    localStorage.setItem(K_ACCESS, access);
    localStorage.setItem(K_REFRESH, refresh);
    localStorage.setItem(K_USER, JSON.stringify(user));
  }

  function clearSession() {
    localStorage.removeItem(K_ACCESS);
    localStorage.removeItem(K_REFRESH);
    localStorage.removeItem(K_USER);
    localStorage.removeItem(K_LOANS);
  }

  function getLoans() {
    try {
      return JSON.parse(localStorage.getItem(K_LOANS) || "[]");
    } catch {
      return [];
    }
  }

  function setLoans(list) {
    localStorage.setItem(K_LOANS, JSON.stringify(list));
  }

  function addLoanEntry(entry) {
    const list = getLoans().filter((l) => l.id !== entry.id);
    list.unshift(entry);
    setLoans(list);
  }

  function removeLoanById(id) {
    setLoans(getLoans().filter((l) => l.id !== id));
  }

  async function syncLoansFromServer() {
    const user = getUser();
    if (!user) {
      setLoans([]);
      return [];
    }
    const items = await apiRequest("/books/loans/me");
    const normalized = (items || []).map((item) => ({
      id: item.loan_id,
      book_id: item.book_id,
      title: item.title,
      issued_at: item.issued_at,
      due_date: item.due_date,
    }));
    setLoans(normalized);
    return normalized;
  }

  function parseHash() {
    const raw = (location.hash || "#books").replace(/^#/, "");
    const parts = raw.split("/").filter(Boolean);
    if (parts[0] === "admin") {
      return {
        view: "admin",
        sub: parts[1] || null,
        id: parts[2] || null,
        parts,
        a: parts[1],
        b: parts[2],
      };
    }
    return {
      view: parts[0] || "books",
      a: parts[1],
      b: parts[2],
      sub: null,
      id: null,
      parts,
    };
  }

  const views = [
    "login",
    "register",
    "books",
    "book",
    "authors",
    "author",
    "profile",
    "admin-authors",
    "admin-author",
    "admin-books",
    "admin-book",
  ];

  function showView(name) {
    for (const v of views) {
      const n = el(`view-${v}`);
      if (n) n.hidden = v !== name;
    }
  }

  function updateChrome() {
    const u = getUser();
    const auth = el("nav-auth");
    const docs = el("api-docs-link");
    if (apiRootUrl()) docs.href = `${apiRootUrl()}/docs`;

    if (u) {
      auth.hidden = false;
      document.querySelectorAll(".admin-only").forEach((node) => {
        node.hidden = !u.is_admin;
      });
    } else {
      auth.hidden = true;
      document.querySelectorAll(".admin-only").forEach((node) => {
        node.hidden = true;
      });
    }
  }

  let refreshPromise = null;

  async function doRefresh() {
    const r = localStorage.getItem(K_REFRESH);
    if (!r) return false;
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: r }),
    });
    if (!res.ok) {
      clearSession();
      return false;
    }
    const data = await res.json();
    setSession(data.access_token, data.refresh_token, data.user);
    return true;
  }

  async function refreshTokens() {
    if (!refreshPromise) {
      refreshPromise = doRefresh().finally(() => {
        refreshPromise = null;
      });
    }
    return refreshPromise;
  }

  async function apiRequest(path, options = {}, allowRetry = true) {
    const headers = { ...options.headers };
    const isForm = options.body instanceof FormData;
    if (!isForm && options.body != null && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }
    const access = localStorage.getItem(K_ACCESS);
    if (access) headers.Authorization = `Bearer ${access}`;

    const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

    if (res.status === 401 && allowRetry) {
      const ok = await refreshTokens();
      if (ok) {
        return apiRequest(path, options, false);
      }
      clearSession();
      const h = (location.hash || "").replace("#", "");
      if (h && h !== "login" && h !== "register") {
        location.hash = "login";
      }
    } else if (res.status === 401 && !allowRetry) {
      clearSession();
      const h = (location.hash || "").replace("#", "");
      if (h && h !== "login" && h !== "register") {
        location.hash = "login";
      }
    }

    if (res.status === 204) return null;
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const j = await res.json();
        detail = messageFromErrorBody(j) || detail;
      } catch {
        /* ignore */
      }
      throw new Error(detail);
    }
    return res.json();
  }

  /* ——— Books list ——— */
  const pageBooks = { limit: 10, offset: 0, query: "" };

  async function loadBooks() {
    const p = new URLSearchParams();
    p.set("limit", String(pageBooks.limit));
    p.set("offset", String(pageBooks.offset));
    if (pageBooks.query) p.set("name_query", pageBooks.query);
    const data = await apiRequest(`/books/?${p.toString()}`);

    const ul = el("book-list");
    ul.innerHTML = "";
    for (const b of data.items) {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = `#book/${b.id}`;
      a.innerHTML = `<strong>${esc(b.title)}</strong>
        <div class="meta">Доступно: ${b.available_instances} · ${fmtAuthors(b)}</div>`;
      li.append(a);
      ul.append(li);
    }
    if (!data.items.length) {
      const li = document.createElement("li");
      li.textContent = "Ничего не найдено.";
      ul.append(li);
    }

    const maxPage = Math.max(0, Math.ceil(data.total / data.limit) - 1);
    const cur = Math.floor(data.offset / data.limit);
    el("books-page-info").textContent = `стр. ${cur + 1} из ${maxPage + 1} (всего ${data.total})`;
    el("books-prev").disabled = data.offset <= 0;
    el("books-next").disabled = data.offset + data.items.length >= data.total;
  }

  /* ——— Book detail ——— */
  async function loadBookDetail(id) {
    const b = await apiRequest(`/books/${id}`);
    const box = el("book-detail");
    const loans = getLoans();
    const myLoan = loans.find((l) => l.book_id === id);

    const genres = b.genres?.length ? b.genres.join(", ") : "—";
    const authorsList =
      b.authors?.map((a) => `${esc(a.name)}`).join(", ") || "—";

    box.innerHTML = `
      <h1>${esc(b.title)}</h1>
      <p class="authors">${authorsList}</p>
      <p><strong>Описание</strong></p>
      <p>${esc(b.description)}</p>
      <p><strong>Опубликована:</strong> ${b.publication_date} · <strong>Жанры:</strong> ${esc(genres)}</p>
      <p><strong>Доступно экземпляров:</strong> ${b.available_instances}</p>
      <div class="book-actions" data-book-id="${b.id}"></div>
    `;
    const actions = box.querySelector(".book-actions");

    if (b.available_instances > 0) {
      const take = document.createElement("button");
      take.className = "btn";
      take.type = "button";
      take.textContent = "Взять книгу";
      take.addEventListener("click", async () => {
        take.disabled = true;
        try {
          const out = await apiRequest(`/books/${b.id}/issue`, { method: "POST" });
          addLoanEntry({
            id: out.loan.id,
            book_id: out.loan.book_id,
            title: b.title,
            issued_at: out.loan.issued_at || null,
            due_date: out.loan.due_date,
          });
          msg("Книга оформлена.", true);
          await loadBookDetail(id);
        } catch (e) {
          msg(String(e?.message || e), false);
        } finally {
          take.disabled = false;
        }
      });
      actions.append(take);
    }

    if (myLoan) {
      const ret = document.createElement("button");
      ret.className = "btn btn-ghost";
      ret.type = "button";
      ret.textContent = "Вернуть книгу";
      ret.addEventListener("click", async () => {
        ret.disabled = true;
        try {
          await apiRequest(`/books/loans/${myLoan.id}/return`, { method: "POST" });
          removeLoanById(myLoan.id);
          msg("Книга возвращена.", true);
          await loadBookDetail(id);
        } catch (e) {
          msg(String(e?.message || e), false);
        } finally {
          ret.disabled = false;
        }
      });
      const span = document.createElement("span");
      span.className = "meta";
      span.textContent = `Сдать до: ${formatDisplayDate(myLoan.due_date)}`;
      actions.append(ret, span);
    }

    if (getUser()?.is_admin) {
      const edit = document.createElement("a");
      edit.href = `#admin/books/${b.id}`;
      edit.className = "btn btn-ghost";
      edit.setAttribute("data-nav", "");
      edit.textContent = "Редактировать";
      actions.append(edit);
    }
  }

  /* ——— Authors list ——— */
  const pageAuthors = { limit: 10, offset: 0, query: "" };

  async function loadAuthors() {
    const p = new URLSearchParams();
    p.set("limit", String(pageAuthors.limit));
    p.set("offset", String(pageAuthors.offset));
    if (pageAuthors.query) p.set("name_query", pageAuthors.query);
    const data = await apiRequest(`/authors/?${p.toString()}`);

    const ul = el("author-list");
    ul.innerHTML = "";
    for (const a of data.items) {
      const li = document.createElement("li");
      const lnk = document.createElement("a");
      lnk.href = `#author/${a.id}`;
      lnk.innerHTML = `<strong>${esc(a.name)}</strong>
        <div class="meta">Книг: ${a.books?.length ?? 0}</div>`;
      li.append(lnk);
      ul.append(li);
    }
    if (!data.items.length) {
      const li = document.createElement("li");
      li.textContent = "Нет авторов.";
      ul.append(li);
    }
    const maxPage = Math.max(0, Math.ceil(data.total / data.limit) - 1);
    const cur = Math.floor(data.offset / data.limit);
    el("authors-page-info").textContent = `стр. ${cur + 1} из ${maxPage + 1} (всего ${data.total})`;
    el("authors-prev").disabled = data.offset <= 0;
    el("authors-next").disabled = data.offset + data.items.length >= data.total;
  }

  async function loadAuthorDetail(id) {
    const a = await apiRequest(`/authors/${id}`);
    const box = el("author-detail");
    const books = (a.books || [])
      .map(
        (b) =>
          `<li><a href="#book/${b.id}" data-nav>${esc(b.title)}</a> — ${b.publication_date} (${b.available_instances} в наличии)</li>`
      )
      .join("");
    box.innerHTML = `
      <h1>${esc(a.name)}</h1>
      <p>${esc(a.biography)}</p>
      <p><strong>День рождения:</strong> ${a.birthday}</p>
      <h2 class="h2">Книги</h2>
      <ul class="list">${books || "<li>Книг нет.</li>"}</ul>
    `;
    if (getUser()?.is_admin) {
      const bar = document.createElement("div");
      bar.className = "detail-admin-bar";
      const edit = document.createElement("a");
      edit.href = `#admin/authors/${a.id}`;
      edit.className = "btn btn-ghost";
      edit.setAttribute("data-nav", "");
      edit.textContent = "Редактировать";
      bar.append(edit);
      box.insertBefore(bar, box.firstChild);
    }
  }

  /* ——— Profile ——— */
  async function loadProfile() {
    const u = getUser();
    if (!u) return;
    const box = el("profile-content");
    try {
      const me = await apiRequest("/users/me");
      box.innerHTML = `<p><strong>Имя:</strong> ${esc(me.username)}</p>
        <p><strong>Email:</strong> ${me.email ? esc(me.email) : "—"}</p>
        <p><strong>Роль:</strong> ${me.is_admin ? "администратор" : "читатель"}</p>
        <p class="meta">ID: ${me.id}</p>`;
    } catch (e) {
      box.textContent = String(e?.message || e);
    }
    const ul = el("loans-list");
    ul.innerHTML = "";
    const loans = await syncLoansFromServer();
    if (!loans.length) {
      const li = document.createElement("li");
      li.textContent = "Сейчас нет взятых книг.";
      ul.append(li);
      return;
    }
    for (const l of loans) {
      const li = document.createElement("li");
      li.innerHTML = `<div class="card loan-card">
        <strong>${esc(l.title)}</strong>
        <div class="meta loan-meta">Взята: ${esc(formatDisplayDate(l.issued_at))} · Сдать до: ${esc(formatDisplayDate(l.due_date))}</div>
        <div class="loan-actions">
          <a href="#book/${l.book_id}" class="btn btn-ghost" data-nav>Открыть книгу</a>
          <button type="button" class="btn" data-loan-return="${esc(l.id)}">Вернуть</button>
        </div>
      </div>`;
      li.querySelector("[data-loan-return]")?.addEventListener("click", async (event) => {
        const button = event.currentTarget;
        const loanId = button?.getAttribute("data-loan-return");
        if (!loanId) return;
        button.disabled = true;
        try {
          await apiRequest(`/books/loans/${loanId}/return`, { method: "POST" });
          removeLoanById(loanId);
          msg("Книга возвращена.", true);
          await loadProfile();
        } catch (e) {
          msg(String(e?.message || e), false);
        } finally {
          button.disabled = false;
        }
      });
      ul.append(li);
    }
  }

  function formatDisplayDate(value) {
    if (!value) return "—";
    const dt = new Date(value);
    if (Number.isNaN(dt.getTime())) return String(value);
    return dt.toLocaleDateString("ru-RU");
  }

  function esc(s) {
    if (s == null) return "";
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function fmtAuthors(b) {
    if (!b.authors?.length) return "";
    return b.authors.map((a) => a.name).join(", ");
  }

  function isUuid(s) {
    return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
      String(s || "")
    );
  }

  const pageAdminAuthors = { limit: 15, offset: 0, query: "" };
  const pageAdminBooks = { limit: 15, offset: 0, query: "" };

  async function loadAdminAuthorsPage() {
    const p = new URLSearchParams();
    p.set("limit", String(pageAdminAuthors.limit));
    p.set("offset", String(pageAdminAuthors.offset));
    if (pageAdminAuthors.query) p.set("name_query", pageAdminAuthors.query);
    const data = await apiRequest(`/authors/?${p.toString()}`);

    const ul = el("admin-authors-list");
    if (!ul) return;
    ul.innerHTML = "";
    for (const a of data.items) {
      const li = document.createElement("li");
      const lnk = document.createElement("a");
      lnk.href = `#admin/authors/${a.id}`;
      lnk.setAttribute("data-nav", "");
      lnk.innerHTML = `<strong>${esc(a.name)}</strong>
        <div class="meta">ID: ${a.id} · книг: ${a.books?.length ?? 0} · <span class="admin-edit-hint">редактировать</span></div>`;
      li.append(lnk);
      ul.append(li);
    }
    if (!data.items.length) {
      const li = document.createElement("li");
      li.className = "meta";
      li.textContent = "Список пуст.";
      ul.append(li);
    }
    const maxPage = Math.max(0, Math.ceil(data.total / data.limit) - 1);
    const cur = Math.floor(data.offset / data.limit);
    el("admin-authors-page-info").textContent = `стр. ${cur + 1} из ${maxPage + 1} (всего ${data.total})`;
    el("admin-authors-prev").disabled = data.offset <= 0;
    el("admin-authors-next").disabled = data.offset + data.items.length >= data.total;
  }

  async function loadAdminAuthorEdit(authorId) {
    const meta = el("admin-author-meta");
    const form = el("form-admin-author-edit");
    if (!meta || !form) return;
    form.hidden = true;
    if (!isUuid(authorId)) {
      meta.textContent = "Некорректный идентификатор.";
      return;
    }
    try {
      const a = await apiRequest(`/authors/${authorId}`);
      el("admin-author-edit-id").value = a.id;
      const fe = form.elements;
      fe.namedItem("name").value = a.name;
      fe.namedItem("biography").value = a.biography;
      fe.namedItem("birthday").value = a.birthday;
      meta.textContent = `ID: ${a.id}`;
      form.hidden = false;
    } catch (e) {
      meta.textContent = String(e?.message || e);
    }
  }

  async function loadAdminBooksPage() {
    const p = new URLSearchParams();
    p.set("limit", String(pageAdminBooks.limit));
    p.set("offset", String(pageAdminBooks.offset));
    if (pageAdminBooks.query) p.set("name_query", pageAdminBooks.query);
    const data = await apiRequest(`/books/?${p.toString()}`);

    const ul = el("admin-books-list");
    if (!ul) return;
    ul.innerHTML = "";
    for (const b of data.items) {
      const li = document.createElement("li");
      const lnk = document.createElement("a");
      lnk.href = `#admin/books/${b.id}`;
      lnk.setAttribute("data-nav", "");
      lnk.innerHTML = `<strong>${esc(b.title)}</strong>
        <div class="meta">ID: ${b.id} · в наличии: ${b.available_instances} · ${esc(fmtAuthors(b) || "—")}</div>`;
      li.append(lnk);
      ul.append(li);
    }
    if (!data.items.length) {
      const li = document.createElement("li");
      li.className = "meta";
      li.textContent = "Список пуст.";
      ul.append(li);
    }
    const maxPage = Math.max(0, Math.ceil(data.total / data.limit) - 1);
    const cur = Math.floor(data.offset / data.limit);
    el("admin-books-page-info").textContent = `стр. ${cur + 1} из ${maxPage + 1} (всего ${data.total})`;
    el("admin-books-prev").disabled = data.offset <= 0;
    el("admin-books-next").disabled = data.offset + data.items.length >= data.total;
  }

  async function loadAdminBookEdit(bookId) {
    const meta = el("admin-book-meta");
    const form = el("form-admin-book-edit");
    const authHint = el("admin-book-authors-hint");
    if (!meta || !form) return;
    form.hidden = true;
    if (authHint) {
      authHint.setAttribute("hidden", "");
      authHint.textContent = "";
    }
    if (!isUuid(bookId)) {
      meta.textContent = "Некорректный идентификатор.";
      return;
    }
    try {
      const b = await apiRequest(`/books/${bookId}`);
      el("admin-book-edit-id").value = b.id;
      const fe = form.elements;
      fe.namedItem("title").value = b.title;
      fe.namedItem("description").value = b.description;
      fe.namedItem("publication_date").value = b.publication_date;
      fe.namedItem("genres").value = (b.genres && b.genres.length ? b.genres : []).join(", ");
      fe.namedItem("available_instances").value = String(b.available_instances);
      const an = b.authors?.map((x) => x.name).join(", ") || "—";
      if (authHint) {
        authHint.textContent = `Авторы: ${an}`;
        authHint.removeAttribute("hidden");
      }
      meta.textContent = `ID: ${b.id}`;
      form.hidden = false;
    } catch (e) {
      if (authHint) {
        authHint.setAttribute("hidden", "");
        authHint.textContent = "";
      }
      meta.textContent = String(e?.message || e);
    }
  }

  async function route() {
    msg("");
    updateChrome();
    const u = getUser();
    const { view, a, sub, id } = parseHash();

    const needAuth = !["login", "register"].includes(view);
    if (needAuth && !u) {
      if (location.hash !== "#login") location.replace("#login");
      showView("login");
      return;
    }
    if (!needAuth && u && (view === "login" || view === "register")) {
      location.replace("#books");
      return;
    }
    if (view === "login") {
      showView("login");
      return;
    }
    if (view === "register") {
      showView("register");
      return;
    }
    if (view === "admin") {
      if (!u || !u.is_admin) {
        location.replace("#books");
        return;
      }
      if (!sub) {
        location.replace("#books");
        return;
      }
      if (sub === "authors" && !id) {
        showView("admin-authors");
        await loadAdminAuthorsPage();
        return;
      }
      if (sub === "authors" && id) {
        showView("admin-author");
        await loadAdminAuthorEdit(id);
        return;
      }
      if (sub === "books" && !id) {
        showView("admin-books");
        await loadAdminBooksPage();
        return;
      }
      if (sub === "books" && id) {
        showView("admin-book");
        await loadAdminBookEdit(id);
        return;
      }
      location.replace("#books");
      return;
    }
    if (view === "books") {
      showView("books");
      await loadBooks();
      return;
    }
    if (view === "book" && a) {
      showView("book");
      try {
        await loadBookDetail(a);
      } catch (e) {
        el("book-detail").innerHTML = `<p class="msg">${esc(String(e?.message || e))}</p>`;
      }
      return;
    }
    if (view === "authors") {
      showView("authors");
      await loadAuthors();
      return;
    }
    if (view === "author" && a) {
      showView("author");
      try {
        await loadAuthorDetail(a);
      } catch (e) {
        el("author-detail").innerHTML = `<p class="msg">${esc(String(e?.message || e))}</p>`;
      }
      return;
    }
    if (view === "profile") {
      showView("profile");
      await loadProfile();
      return;
    }
    location.replace("#books");
  }

  /* Events */
  document.getElementById("btn-logout")?.addEventListener("click", () => {
    const r = localStorage.getItem(K_REFRESH);
    if (r) {
      fetch(`${API_BASE}/auth/logout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: r }),
      }).catch(() => {});
    }
    clearSession();
    msg("Вы вышли.", true);
    location.hash = "login";
    route();
  });

  el("form-login")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const payload = {
      identifier: String(fd.get("identifier") || "").trim(),
      password: String(fd.get("password") || ""),
    };
    try {
      const data = await apiRequest("/auth/login", { method: "POST", body: JSON.stringify(payload) });
      setSession(data.access_token, data.refresh_token, data.user);
      await syncLoansFromServer();
      msg("Вход выполнен.", true);
      location.hash = "books";
    } catch (err) {
      msg(String(err?.message || err), false);
    }
  });

  el("form-register")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const email = String(fd.get("email") || "").trim();
    const payload = {
      username: String(fd.get("username") || "").trim(),
      password: String(fd.get("password") || ""),
      email: email || null,
    };
    try {
      await apiRequest("/auth/register", { method: "POST", body: JSON.stringify(payload) });
      msg("Аккаунт создан. Войдите с теми же данными.", true);
      location.hash = "login";
    } catch (err) {
      msg(String(err?.message || err), false);
    }
  });

  el("form-books-search")?.addEventListener("submit", (e) => {
    e.preventDefault();
    const q = new FormData(e.target).get("q");
    pageBooks.query = String(q || "").trim();
    pageBooks.offset = 0;
    loadBooks().catch((err) => msg(String(err?.message || err), false));
  });

  el("books-prev")?.addEventListener("click", () => {
    pageBooks.offset = Math.max(0, pageBooks.offset - pageBooks.limit);
    loadBooks().catch((err) => msg(String(err?.message || err), false));
  });
  el("books-next")?.addEventListener("click", () => {
    pageBooks.offset += pageBooks.limit;
    loadBooks().catch((err) => msg(String(err?.message || err), false));
  });

  el("form-authors-search")?.addEventListener("submit", (e) => {
    e.preventDefault();
    const q = new FormData(e.target).get("q");
    pageAuthors.query = String(q || "").trim();
    pageAuthors.offset = 0;
    loadAuthors().catch((err) => msg(String(err?.message || err), false));
  });
  el("authors-prev")?.addEventListener("click", () => {
    pageAuthors.offset = Math.max(0, pageAuthors.offset - pageAuthors.limit);
    loadAuthors().catch((err) => msg(String(err?.message || err), false));
  });
  el("authors-next")?.addEventListener("click", () => {
    pageAuthors.offset += pageAuthors.limit;
    loadAuthors().catch((err) => msg(String(err?.message || err), false));
  });

  el("form-admin-author-create")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const payload = {
      name: String(fd.get("name") || "").trim(),
      biography: String(fd.get("biography") || "").trim(),
      birthday: String(fd.get("birthday") || ""),
    };
    try {
      const a = await apiRequest("/authors/", { method: "POST", body: JSON.stringify(payload) });
      msg(`Автор «${a.name}» создан. ID для привязки книги: ${a.id}`, true);
      e.target.reset();
      loadAdminAuthorsPage().catch((err) => msg(String(err?.message || err), false));
    } catch (err) {
      msg(String(err?.message || err), false);
    }
  });

  el("form-admin-author-edit")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const id = String(fd.get("id") || el("admin-author-edit-id")?.value || "").trim();
    const payload = {
      name: String(fd.get("name") || "").trim(),
      biography: String(fd.get("biography") || "").trim(),
      birthday: String(fd.get("birthday") || ""),
    };
    if (!isUuid(id)) {
      msg("Некорректный ID автора.", false);
      return;
    }
    try {
      const a = await apiRequest(`/authors/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
      msg(`Сохранено: «${a.name}»`, true);
    } catch (err) {
      msg(String(err?.message || err), false);
    }
  });

  el("btn-admin-author-delete")?.addEventListener("click", async () => {
    const id = String(el("admin-author-edit-id")?.value || "").trim();
    if (!isUuid(id)) {
      msg("Некорректный ID автора.", false);
      return;
    }
    if (!window.confirm("Удалить автора? Это действие нельзя отменить.")) {
      return;
    }
    try {
      await apiRequest(`/authors/${id}`, { method: "DELETE" });
      msg("Автор удалён.", true);
      location.hash = "admin/authors";
    } catch (err) {
      msg(String(err?.message || err), false);
    }
  });

  el("form-admin-book-create")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const genresRaw = String(fd.get("genres") || "").trim();
    const genres = genresRaw
      .split(/[,;]/)
      .map((g) => g.trim())
      .filter(Boolean);
    const authorId = String(fd.get("author_id") || "").trim();
    const payload = {
      title: String(fd.get("title") || "").trim(),
      description: String(fd.get("description") || "").trim(),
      publication_date: String(fd.get("publication_date") || ""),
      genres,
      author_ids: [authorId],
      available_instances: Number(fd.get("available_instances") ?? 0),
    };
    try {
      const b = await apiRequest("/books/", { method: "POST", body: JSON.stringify(payload) });
      msg(`Книга «${b.title}» создана. ID: ${b.id}`, true);
      e.target.reset();
      loadAdminBooksPage().catch((err) => msg(String(err?.message || err), false));
    } catch (err) {
      msg(String(err?.message || err), false);
    }
  });

  el("form-admin-book-edit")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const id = String(fd.get("id") || el("admin-book-edit-id")?.value || "").trim();
    if (!isUuid(id)) {
      msg("Некорректный ID книги.", false);
      return;
    }
    const genresRaw = String(fd.get("genres") || "").trim();
    const genres = genresRaw
      .split(/[,;]/)
      .map((g) => g.trim())
      .filter(Boolean);
    const payload = {
      title: String(fd.get("title") || "").trim(),
      description: String(fd.get("description") || "").trim(),
      publication_date: String(fd.get("publication_date") || ""),
      genres,
      available_instances: Number(fd.get("available_instances") ?? 0),
    };
    try {
      const b = await apiRequest(`/books/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
      msg(`Сохранено: «${b.title}»`, true);
    } catch (err) {
      msg(String(err?.message || err), false);
    }
  });

  el("btn-admin-book-delete")?.addEventListener("click", async () => {
    const id = String(el("admin-book-edit-id")?.value || "").trim();
    if (!isUuid(id)) {
      msg("Некорректный ID книги.", false);
      return;
    }
    if (!window.confirm("Удалить книгу? Это действие нельзя отменить.")) {
      return;
    }
    try {
      await apiRequest(`/books/${id}`, { method: "DELETE" });
      msg("Книга удалена.", true);
      location.hash = "admin/books";
    } catch (err) {
      msg(String(err?.message || err), false);
    }
  });

  el("form-admin-authors-search")?.addEventListener("submit", (e) => {
    e.preventDefault();
    const q = new FormData(e.target).get("q");
    pageAdminAuthors.query = String(q || "").trim();
    pageAdminAuthors.offset = 0;
    loadAdminAuthorsPage().catch((err) => msg(String(err?.message || err), false));
  });
  el("admin-authors-prev")?.addEventListener("click", () => {
    pageAdminAuthors.offset = Math.max(0, pageAdminAuthors.offset - pageAdminAuthors.limit);
    loadAdminAuthorsPage().catch((err) => msg(String(err?.message || err), false));
  });
  el("admin-authors-next")?.addEventListener("click", () => {
    pageAdminAuthors.offset += pageAdminAuthors.limit;
    loadAdminAuthorsPage().catch((err) => msg(String(err?.message || err), false));
  });

  el("form-admin-books-search")?.addEventListener("submit", (e) => {
    e.preventDefault();
    const q = new FormData(e.target).get("q");
    pageAdminBooks.query = String(q || "").trim();
    pageAdminBooks.offset = 0;
    loadAdminBooksPage().catch((err) => msg(String(err?.message || err), false));
  });
  el("admin-books-prev")?.addEventListener("click", () => {
    pageAdminBooks.offset = Math.max(0, pageAdminBooks.offset - pageAdminBooks.limit);
    loadAdminBooksPage().catch((err) => msg(String(err?.message || err), false));
  });
  el("admin-books-next")?.addEventListener("click", () => {
    pageAdminBooks.offset += pageAdminBooks.limit;
    loadAdminBooksPage().catch((err) => msg(String(err?.message || err), false));
  });

  document.querySelectorAll("[data-nav]").forEach((a) => {
    a.addEventListener("click", () => {
      setTimeout(() => {
        if (!getUser() && !["login", "register"].includes(parseHash().view)) {
          return;
        }
        msg("");
      }, 0);
    });
  });

  window.addEventListener("hashchange", () => {
    route().catch((err) => msg(String(err?.message || err), false));
  });

  if (!location.hash) location.hash = "books";
  route().catch((err) => msg(String(err?.message || err), false));
})();
