(function () {
  "use strict";

  function resolveApiBase() {
    if (window.location.protocol === "file:") {
      const fromQuery = new URLSearchParams(window.location.search).get("api");
      const base = (fromQuery || "http://127.0.0.1:8000").replace(/\/$/, "");
      return `${base}/api`;
    }
    return `${window.location.origin}/api`;
  }

  const API = resolveApiBase();

  const DEFAULT_CLI_COMMAND =
    'python main.py --keyword plumber --city "Austin, TX" --max-pages 1';

  let activeRunId = null;
  let pollTimer = null;
  let lastRunSnapshot = null;
  let tableSort = { key: "company_name", order: "asc" };
  let tablePage = 1;

  const SORTABLE_RESULT_COLUMNS = new Set(["company_name", "category"]);

  function normalizeTableSort() {
    if (!SORTABLE_RESULT_COLUMNS.has(tableSort.key)) {
      tableSort.key = "company_name";
      tableSort.order = "asc";
    }
  }

  const PER_PAGE_STORAGE = "scraper_results_per_page";
  const PER_PAGE_OPTIONS = [10, 25, 30, 50, 100];
  const DEFAULT_PER_PAGE = 30;

  function getPerPage() {
    const sel = $("#per-page-select");
    if (!sel) return DEFAULT_PER_PAGE;
    const v = parseInt(sel.value, 10);
    return PER_PAGE_OPTIONS.includes(v) ? v : DEFAULT_PER_PAGE;
  }

  function syncResultsActivityDropdownClass() {
    const activity = $("#results-activity");
    if (!activity) return;
    const openCount = activity.querySelectorAll(".select-custom.is-open").length;
    activity.classList.toggle(
      "results-activity--dropdown-open",
      openCount > 0
    );
  }

  function setupPerPageCustomSelect() {
    const root = $("#per-page-root");
    const trigger = $("#per-page-trigger");
    const list = $("#per-page-list");
    const hidden = $("#per-page-select");
    const label = $("#per-page-label");
    if (!root || !trigger || !list || !hidden || !label) return;

    function setValue(val) {
      const s = String(val);
      hidden.value = s;
      label.textContent = s;
      list.querySelectorAll("li").forEach((li) => {
        const v = li.getAttribute("data-value") ?? "";
        li.classList.toggle("is-selected", v === s);
      });
    }

    function close() {
      root.classList.remove("is-open");
      list.classList.add("hidden");
      trigger.setAttribute("aria-expanded", "false");
      syncResultsActivityDropdownClass();
    }

    function open() {
      root.classList.add("is-open");
      list.classList.remove("hidden");
      trigger.setAttribute("aria-expanded", "true");
      syncResultsActivityDropdownClass();
    }

    trigger.addEventListener("click", (e) => {
      e.stopPropagation();
      if (list.classList.contains("hidden")) open();
      else close();
    });

    list.querySelectorAll("li").forEach((li) => {
      li.addEventListener("click", (e) => {
        e.stopPropagation();
        const v = li.getAttribute("data-value") ?? "";
        if (hidden.value === v) {
          close();
          return;
        }
        setValue(v);
        localStorage.setItem(PER_PAGE_STORAGE, v);
        tablePage = 1;
        loadResultsTable();
        close();
      });
    });

    document.addEventListener("click", (e) => {
      if (!root.contains(e.target)) close();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && root.classList.contains("is-open")) {
        close();
        trigger.focus();
      }
    });

    const saved = localStorage.getItem(PER_PAGE_STORAGE);
    const n = saved ? parseInt(saved, 10) : NaN;
    if (PER_PAGE_OPTIONS.includes(n)) {
      setValue(String(n));
    } else {
      setValue(String(DEFAULT_PER_PAGE));
    }
  }

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  function syncSortHeaderState() {
    $$(".th-sort-btn").forEach((btn) => {
      const key = btn.getAttribute("data-sort");
      const th = btn.closest("th");
      btn.classList.remove("is-sorted-asc", "is-sorted-desc");
      if (th) th.removeAttribute("aria-sort");
      if (tableSort.key === key) {
        const asc = tableSort.order === "asc";
        btn.classList.add(asc ? "is-sorted-asc" : "is-sorted-desc");
        if (th) th.setAttribute("aria-sort", asc ? "ascending" : "descending");
      }
    });
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function formatTime(sec) {
    if (sec == null || Number.isNaN(sec)) return "—";
    if (sec < 60) return `${Math.round(sec)}s`;
    const m = Math.floor(sec / 60);
    const s = Math.round(sec % 60);
    return `${m}m ${s}s`;
  }

  function formatDt(iso) {
    if (!iso) return "—";
    try {
      return new Date(iso).toLocaleString();
    } catch {
      return iso;
    }
  }

  function truncateUrl(url, max) {
    if (!url) return { short: "—", full: "" };
    const u = String(url);
    if (u.length <= max) return { short: escapeHtml(u), full: u };
    return {
      short: escapeHtml(u.slice(0, max)) + "…",
      full: u,
    };
  }

  function statusPillClass(status) {
    if (status === "running" || status === "queued") return "status-pill status-running";
    if (status === "completed") return "status-pill status-completed";
    if (status === "completed_with_warnings") return "status-pill status-warn";
    if (status === "failed") return "status-pill status-failed";
    return "status-pill status-idle";
  }

  function statusLabel(status) {
    if (status === "queued") return "Queued";
    if (status === "running") return "Running";
    if (status === "completed") return "Completed";
    if (status === "completed_with_warnings") return "Completed (warnings)";
    if (status === "failed") return "Failed";
    return "Idle";
  }

  async function refreshRun(id) {
    try {
      const res = await fetch(`${API}/runs/${id}`);
      if (!res.ok) return;
      const run = await res.json();
      lastRunSnapshot = run;
      renderRun(run);
    } catch (e) {
      console.error(e);
    }
  }

  function startPoll() {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(async () => {
      if (!activeRunId) return;
      const res = await fetch(`${API}/runs/${activeRunId}`);
      if (!res.ok) return;
      const run = await res.json();
      lastRunSnapshot = run;
      renderRun(run);
      if (
        run.status === "running" ||
        run.status === "queued"
      ) {
        await loadResultsTable();
      }
      if (
        run.status !== "running" &&
        run.status !== "queued"
      ) {
        clearInterval(pollTimer);
        pollTimer = null;
        await loadResultsTable();
      }
    }, 2000);
  }

  function renderRun(run) {
    $("#status-label").className = statusPillClass(run.status);
    $("#status-label").textContent = statusLabel(run.status);

    $("#status-started").textContent = run.started_at
      ? `Started: ${formatDt(run.started_at)}`
      : "";

    const total = run.pages_total || 1;
    const done = run.pages_processed || 0;
    const pct =
      run.status === "running" || run.status === "queued"
        ? Math.min(100, Math.round((done / total) * 100))
        : run.status === "completed" ||
            run.status === "completed_with_warnings" ||
            run.status === "failed"
          ? 100
          : 0;
    $("#progress-bar").style.width = `${pct}%`;

    let progText = "";
    if (run.status === "queued") progText = "Job queued…";
    else if (run.status === "running")
      progText = `${done} of ${total} pages processed`;
    else if (run.status === "completed")
      progText = `Completed: ${done} of ${total} pages processed`;
    else if (run.status === "completed_with_warnings")
      progText = `Finished with warnings: ${done} of ${total} pages processed`;
    else if (run.status === "failed")
      progText = "Run failed before completion.";
    else progText = "No active job.";
    $("#progress-text").textContent = progText;

    $("#run-log").textContent = run.log_snippet || "";

    $("#metric-unique").textContent =
      run.unique_records_count != null ? run.unique_records_count : "—";
    $("#metric-pages").textContent =
      run.pages_processed != null
        ? `${run.pages_parsed_ok ?? 0} ok / ${run.pages_processed} total`
        : "—";
    $("#metric-blocked").textContent =
      run.pages_blocked != null ? run.pages_blocked : "—";
    $("#metric-time").textContent = formatTime(run.elapsed_seconds);

    $("#sum-keyword").textContent = run.keyword ?? "—";
    $("#sum-city").textContent = run.city ?? "—";
    $("#sum-req").textContent = run.max_pages ?? "—";
    $("#sum-parsed").textContent =
      run.pages_parsed_ok != null ? String(run.pages_parsed_ok) : "—";
    $("#sum-blocked").textContent =
      run.pages_blocked != null ? String(run.pages_blocked) : "—";
    $("#sum-raw").textContent =
      run.raw_records_count != null ? String(run.raw_records_count) : "—";
    $("#sum-uniq").textContent =
      run.unique_records_count != null ? String(run.unique_records_count) : "—";

    const files = [];
    if (run.export_csv) files.push("CSV");
    if (run.export_xlsx) files.push("Excel");
    $("#sum-files").textContent = files.length ? files.join(", ") : "—";
    $("#sum-final").textContent = statusLabel(run.status);

    const alerts = $("#alerts");
    alerts.innerHTML = "";
    $("#form-errors").classList.add("hidden");
    $("#form-errors").textContent = "";

    if (run.warnings && run.warnings.length) {
      run.warnings.forEach((w) => {
        const d = document.createElement("div");
        d.className = "alert alert-warn";
        d.textContent = w;
        alerts.appendChild(d);
      });
    }
    if (run.error_message) {
      const d = document.createElement("div");
      d.className = "alert alert-error";
      d.textContent = run.error_message;
      alerts.appendChild(d);
    }

    const terminal =
      run.status === "completed" ||
      run.status === "completed_with_warnings" ||
      (run.status === "failed" && (run.unique_records_count || 0) > 0);
    const hasData = (run.unique_records_count || 0) > 0;

    const csvA = $("#dl-csv");
    const xlsxA = $("#dl-xlsx");
    if (terminal && hasData && run.export_csv) {
      csvA.href = `${API}/runs/${run.id}/download.csv`;
      csvA.classList.remove("hidden");
    } else {
      csvA.classList.add("hidden");
      csvA.removeAttribute("href");
    }
    if (terminal && hasData && run.export_xlsx) {
      xlsxA.href = `${API}/runs/${run.id}/download.xlsx`;
      xlsxA.classList.remove("hidden");
    } else {
      xlsxA.classList.add("hidden");
      xlsxA.removeAttribute("href");
    }

    $("#results-empty").classList.toggle("hidden", !!activeRunId);
    $("#results-none").classList.add("hidden");
    $("#results-activity").classList.toggle("hidden", !activeRunId);
  }

  const RESULT_ROW_FIELDS = [
    "company_name",
    "website",
    "phone",
    "category",
    "address",
    "city",
    "source_url",
  ];

  function resultRowPayloadFromDataset(cb) {
    try {
      const raw = cb.dataset.resultRow;
      if (!raw) return null;
      const o = JSON.parse(raw);
      const out = {};
      for (const k of RESULT_ROW_FIELDS) {
        out[k] = o[k] != null ? String(o[k]) : "";
      }
      return out;
    } catch {
      return null;
    }
  }

  function getResultsRowCheckboxes() {
    return $$("#table-body .results-row-check");
  }

  function getSelectedResultPayloads() {
    return [...getResultsRowCheckboxes()]
      .filter((c) => c.checked)
      .map(resultRowPayloadFromDataset)
      .filter(Boolean);
  }

  function updateResultsBulkUI() {
    const checks = getResultsRowCheckboxes();
    const selectAll = $("#results-select-all");
    const bar = $("#results-bulk-bar");
    const total = checks.length;
    const n = [...checks].filter((c) => c.checked).length;

    if (selectAll) {
      selectAll.disabled = total === 0;
      if (total === 0) {
        selectAll.checked = false;
        selectAll.indeterminate = false;
      } else {
        selectAll.indeterminate = n > 0 && n < total;
        selectAll.checked = n === total;
      }
    }

    if (bar) {
      bar.classList.toggle("hidden", n === 0 || total === 0);
    }

    const countEl = $("#results-selected-count");
    if (countEl) {
      countEl.textContent =
        n === 1 ? "1 row selected" : `${n} rows selected`;
    }
  }

  function setupResultsRowSelection() {
    const selectAll = $("#results-select-all");
    const btnSelectAll = $("#results-select-all-visible");
    const btnDelete = $("#results-delete-selected");
    const body = $("#table-body");
    if (!selectAll || !btnSelectAll || !btnDelete || !body) return;

    selectAll.addEventListener("change", () => {
      const on = selectAll.checked;
      getResultsRowCheckboxes().forEach((c) => {
        c.checked = on;
      });
      updateResultsBulkUI();
    });

    body.addEventListener("change", (e) => {
      const t = e.target;
      if (t && t.classList && t.classList.contains("results-row-check")) {
        updateResultsBulkUI();
      }
    });

    btnSelectAll.addEventListener("click", () => {
      getResultsRowCheckboxes().forEach((c) => {
        c.checked = true;
      });
      updateResultsBulkUI();
    });

    btnDelete.addEventListener("click", async () => {
      if (!activeRunId) return;
      const items = getSelectedResultPayloads();
      if (items.length === 0) return;
      if (
        !window.confirm(
          `Delete ${items.length} row(s) from this run? Export files will be updated. This cannot be undone.`
        )
      ) {
        return;
      }
      try {
        const res = await fetch(
          `${API}/runs/${activeRunId}/results/delete`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ items }),
          }
        );
        if (res.status === 409) {
          window.alert(
            "Cannot delete rows while the run is queued or still running."
          );
          return;
        }
        if (!res.ok) {
          const j = await res.json().catch(() => ({}));
          const msg =
            typeof j.detail === "string" ? j.detail : "Could not delete rows.";
          window.alert(msg);
          return;
        }
        const data = await res.json();
        if ((data.removed || 0) === 0) {
          window.alert(
            "No rows were removed. Refresh and try again if the list changed."
          );
        }
        await refreshRun(activeRunId);
        await loadResultsTable();
      } catch (ex) {
        console.error(ex);
        window.alert("Network error while deleting rows.");
      }
    });
  }

  async function loadResultsTable() {
    if (!activeRunId) return;
    normalizeTableSort();
    const q = $("#filter-q").value.trim();
    const fc = $("#filter-city").value.trim();
    const fcat = $("#filter-category").value.trim();
    const hw = $("#filter-website").value;

    const params = new URLSearchParams({
      page: String(tablePage),
      per_page: String(getPerPage()),
      sort: tableSort.key,
      order: tableSort.order,
      q,
      filter_city: fc,
      filter_category: fcat,
      has_website: hw,
    });

    const res = await fetch(
      `${API}/runs/${activeRunId}/results?${params.toString()}`
    );
    if (!res.ok) return;
    let data = await res.json();
    const per = getPerPage();
    const maxPage = Math.max(1, Math.ceil(data.total / per) || 1);
    if (tablePage > maxPage) {
      tablePage = maxPage;
      return loadResultsTable();
    }

    $("#results-count").textContent =
      data.total === 0
        ? "0 rows (after filters)"
        : `${data.total} row(s) — page ${data.page} · ${data.per_page} per page`;

    const tbody = $("#table-body");
    tbody.innerHTML = "";

    if (data.total === 0 && lastRunSnapshot) {
      $("#results-none").classList.remove("hidden");
    } else {
      $("#results-none").classList.add("hidden");
    }

    for (const row of data.items) {
      const tr = document.createElement("tr");

      const tdCheck = document.createElement("td");
      tdCheck.className = "results-cell-check";
      const rowCb = document.createElement("input");
      rowCb.type = "checkbox";
      rowCb.className = "history-check results-row-check";
      rowCb.setAttribute("aria-label", "Select this row");
      rowCb.dataset.resultRow = JSON.stringify({
        company_name: row.company_name ?? "",
        website: row.website ?? "",
        phone: row.phone ?? "",
        category: row.category ?? "",
        address: row.address ?? "",
        city: row.city ?? "",
        source_url: row.source_url ?? "",
      });
      tdCheck.appendChild(rowCb);
      tr.appendChild(tdCheck);

      const tdName = document.createElement("td");
      tdName.textContent = row.company_name || "";
      tr.appendChild(tdName);

      const tdWeb = document.createElement("td");
      tdWeb.className = "url-cell";
      if (row.website) {
        const a = document.createElement("a");
        a.href = row.website;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        const wi = truncateUrl(row.website, 36);
        a.innerHTML = wi.short;
        tdWeb.appendChild(a);
        const wrap = document.createElement("div");
        wrap.className = "cell-actions";
        const b = document.createElement("button");
        b.type = "button";
        b.textContent = "Copy website";
        b.addEventListener("click", () => {
          navigator.clipboard.writeText(row.website);
          b.textContent = "Copied";
          setTimeout(() => {
            b.textContent = "Copy website";
          }, 1500);
        });
        wrap.appendChild(b);
        tdWeb.appendChild(wrap);
      } else {
        tdWeb.textContent = "—";
      }
      tr.appendChild(tdWeb);

      const tdPhone = document.createElement("td");
      if (row.phone) {
        tdPhone.appendChild(document.createTextNode(row.phone));
        const wrap = document.createElement("div");
        wrap.className = "cell-actions";
        const b = document.createElement("button");
        b.type = "button";
        b.textContent = "Copy phone";
        b.addEventListener("click", () => {
          navigator.clipboard.writeText(row.phone);
          b.textContent = "Copied";
          setTimeout(() => {
            b.textContent = "Copy phone";
          }, 1500);
        });
        wrap.appendChild(b);
        tdPhone.appendChild(wrap);
      } else {
        tdPhone.textContent = "—";
      }
      tr.appendChild(tdPhone);

      const tdCat = document.createElement("td");
      tdCat.textContent = row.category || "";
      tr.appendChild(tdCat);

      const tdAddr = document.createElement("td");
      tdAddr.textContent = row.address || "";
      tr.appendChild(tdAddr);

      const tdCity = document.createElement("td");
      tdCity.textContent = row.city || "";
      tr.appendChild(tdCity);

      const tdSrc = document.createElement("td");
      tdSrc.className = "url-cell";
      if (row.source_url) {
        const a = document.createElement("a");
        a.href = row.source_url;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        a.title = row.source_url;
        const ui = truncateUrl(row.source_url, 42);
        a.innerHTML = ui.short;
        tdSrc.appendChild(a);
      } else {
        tdSrc.textContent = "—";
      }
      tr.appendChild(tdSrc);

      tbody.appendChild(tr);
    }

    updateResultsBulkUI();
    renderPagination(data.total, data.page, data.per_page);
    syncSortHeaderState();
  }

  function renderPagination(total, page, per) {
    const el = $("#pagination");
    if (total <= per) {
      el.classList.add("hidden");
      return;
    }
    el.classList.remove("hidden");
    const pages = Math.ceil(total / per);
    el.innerHTML = "";
    const prev = document.createElement("button");
    prev.type = "button";
    prev.className = "btn btn-secondary btn-sm";
    prev.textContent = "Previous";
    prev.disabled = page <= 1;
    prev.addEventListener("click", () => {
      tablePage = Math.max(1, page - 1);
      loadResultsTable();
    });
    const next = document.createElement("button");
    next.type = "button";
    next.className = "btn btn-secondary btn-sm";
    next.textContent = "Next";
    next.disabled = page >= pages;
    next.addEventListener("click", () => {
      tablePage = Math.min(pages, page + 1);
      loadResultsTable();
    });
    const info = document.createElement("span");
    info.textContent = `Page ${page} of ${pages}`;
    el.append(prev, info, next);
  }

  function getHistoryRowCheckboxes() {
    return $$("#history-body .history-row-check");
  }

  function updateHistoryBulkUI() {
    const checks = getHistoryRowCheckboxes();
    const selectAll = $("#history-select-all");
    const bar = $("#history-bulk-bar");
    const total = checks.length;
    const n = [...checks].filter((c) => c.checked).length;

    if (selectAll) {
      selectAll.disabled = total === 0;
      if (total === 0) {
        selectAll.checked = false;
        selectAll.indeterminate = false;
      } else {
        selectAll.indeterminate = n > 0 && n < total;
        selectAll.checked = n === total;
      }
    }

    if (bar) {
      bar.classList.toggle("hidden", n === 0 || total === 0);
    }

    const countEl = $("#history-selected-count");
    if (countEl) {
      countEl.textContent =
        n === 1 ? "1 run selected" : `${n} runs selected`;
    }
  }

  function setupHistoryBulkActions() {
    const selectAll = $("#history-select-all");
    const btnSelectAll = $("#history-select-all-visible");
    const btnDelete = $("#history-delete-selected");
    const body = $("#history-body");
    if (!selectAll || !btnSelectAll || !btnDelete || !body) return;

    selectAll.addEventListener("change", () => {
      const on = selectAll.checked;
      getHistoryRowCheckboxes().forEach((c) => {
        c.checked = on;
      });
      updateHistoryBulkUI();
    });

    body.addEventListener("change", (e) => {
      const t = e.target;
      if (t && t.classList && t.classList.contains("history-row-check")) {
        updateHistoryBulkUI();
      }
    });

    btnSelectAll.addEventListener("click", () => {
      getHistoryRowCheckboxes().forEach((c) => {
        c.checked = true;
      });
      updateHistoryBulkUI();
    });

    btnDelete.addEventListener("click", async () => {
      const ids = [...getHistoryRowCheckboxes()]
        .filter((c) => c.checked)
        .map((c) => c.getAttribute("data-run-id"))
        .filter(Boolean);
      if (ids.length === 0) return;
      if (
        !window.confirm(
          `Delete ${ids.length} run(s)? Exported files will be removed. This cannot be undone.`
        )
      ) {
        return;
      }
      try {
        const res = await fetch(`${API}/runs/delete`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ids }),
        });
        if (!res.ok) {
          const j = await res.json().catch(() => ({}));
          const msg =
            typeof j.detail === "string" ? j.detail : "Could not delete runs.";
          window.alert(msg);
          return;
        }
        const data = await res.json();
        const deleted = new Set(data.deleted || []);
        if ((data.skipped || []).length > 0) {
          window.alert(
            `${data.skipped.length} run(s) could not be deleted (missing, or still queued/running).`
          );
        }
        if (activeRunId && deleted.has(activeRunId)) {
          activeRunId = null;
          lastRunSnapshot = null;
          if (pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
          }
          $("#results-activity").classList.add("hidden");
          $("#table-body").innerHTML = "";
          $("#pagination").classList.add("hidden");
          $("#results-empty").classList.remove("hidden");
          $("#results-none").classList.add("hidden");
        }
        await loadHistory();
      } catch (ex) {
        console.error(ex);
        window.alert("Network error while deleting runs.");
      }
    });
  }

  async function loadHistory() {
    const res = await fetch(`${API}/runs?limit=50`);
    if (!res.ok) return;
    const runs = await res.json();
    const body = $("#history-body");
    body.innerHTML = "";
    $("#history-empty").classList.toggle("hidden", runs.length > 0);

    for (const r of runs) {
      const tr = document.createElement("tr");
      const pillClass = statusPillClass(r.status);
      const pillText = escapeHtml(statusLabel(r.status));
      const rid = escapeHtml(r.id);
      tr.innerHTML = `
        <td><input type="checkbox" class="history-check history-row-check" data-run-id="${rid}" aria-label="Select this run" /></td>
        <td>${escapeHtml(r.keyword)}</td>
        <td>${escapeHtml(r.city)}</td>
        <td>${r.max_pages}</td>
        <td><span class="${pillClass}">${pillText}</span></td>
        <td>${formatDt(r.created_at)}</td>
        <td>${r.unique_records_count ?? "—"}</td>
        <td><div class="history-row-actions"><button type="button" class="history-action-link" data-open="${rid}">Open</button></div></td>`;
      body.appendChild(tr);
    }

    body.querySelectorAll("[data-open]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-open");
        openRunFromHistory(id);
      });
    });

    updateHistoryBulkUI();
  }

  async function openRunFromHistory(id) {
    activeRunId = id;
    tablePage = 1;
    $$(".tab").forEach((t) => {
      t.classList.toggle("active", t.dataset.tab === "run");
      t.setAttribute("aria-selected", t.dataset.tab === "run");
    });
    $("#panel-run").classList.remove("hidden");
    $("#panel-history").classList.add("hidden");
    $("#panel-history").hidden = true;
    $("#panel-run").hidden = false;

    await refreshRun(id);
    if (
      lastRunSnapshot &&
      (lastRunSnapshot.status === "running" ||
        lastRunSnapshot.status === "queued")
    ) {
      startPoll();
    }
    await loadResultsTable();
  }

  function setupWebsiteFilterSelect() {
    const root = $("#filter-website-root");
    const trigger = $("#filter-website-trigger");
    const list = $("#filter-website-list");
    const hidden = $("#filter-website");
    const label = $("#filter-website-label");
    if (!root || !trigger || !list || !hidden || !label) return;

    const options = [
      { value: "", text: "Any website" },
      { value: "true", text: "Has website" },
      { value: "false", text: "No website" },
    ];

    function setValue(val) {
      hidden.value = val;
      const opt = options.find((o) => o.value === String(val));
      label.textContent = opt ? opt.text : "Any website";
      list.querySelectorAll("li").forEach((li) => {
        const v = li.getAttribute("data-value") ?? "";
        li.classList.toggle("is-selected", v === String(val));
      });
    }

    function close() {
      root.classList.remove("is-open");
      list.classList.add("hidden");
      trigger.setAttribute("aria-expanded", "false");
      syncResultsActivityDropdownClass();
    }

    function open() {
      root.classList.add("is-open");
      list.classList.remove("hidden");
      trigger.setAttribute("aria-expanded", "true");
      syncResultsActivityDropdownClass();
    }

    trigger.addEventListener("click", (e) => {
      e.stopPropagation();
      if (list.classList.contains("hidden")) open();
      else close();
    });

    list.querySelectorAll("li").forEach((li) => {
      li.addEventListener("click", (e) => {
        e.stopPropagation();
        setValue(li.getAttribute("data-value") ?? "");
        close();
      });
    });

    document.addEventListener("click", (e) => {
      if (!root.contains(e.target)) close();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && root.classList.contains("is-open")) {
        close();
        trigger.focus();
      }
    });

    setValue(hidden.value || "");
  }

  function resetForm() {
    $("#cli-line").value = DEFAULT_CLI_COMMAND;
    $("#fmt-csv").checked = true;
    $("#fmt-xlsx").checked = true;
    $("#form-errors").classList.add("hidden");
    $("#form-errors").textContent = "";
  }

  function setupDashboard() {
    if (!$("#scrape-form")) {
      console.error(
        "Dashboard: #scrape-form not found. Open http://127.0.0.1:8000/ from uvicorn."
      );
      return;
    }

    $$(".tab").forEach((tab) => {
      tab.addEventListener("click", () => {
        const name = tab.dataset.tab;
        $$(".tab").forEach((t) => {
          t.classList.toggle("active", t === tab);
          t.setAttribute("aria-selected", t === tab);
        });
        const runPanel = $("#panel-run");
        const histPanel = $("#panel-history");
        if (name === "run") {
          runPanel.classList.remove("hidden");
          histPanel.classList.add("hidden");
          runPanel.hidden = false;
          histPanel.hidden = true;
        } else {
          runPanel.classList.add("hidden");
          histPanel.classList.remove("hidden");
          runPanel.hidden = true;
          histPanel.hidden = false;
          loadHistory();
        }
      });
    });

    $("#scrape-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const command = $("#cli-line").value.trim();
      const err = $("#form-errors");
      err.classList.add("hidden");
      err.textContent = "";

      if (!command) {
        err.textContent = "Enter a command (same as in the terminal).";
        err.classList.remove("hidden");
        return;
      }

      const startBtn = $("#btn-start");
      startBtn.disabled = true;
      try {
        const res = await fetch(`${API}/runs/cli`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            command,
            export_csv: $("#fmt-csv").checked,
            export_xlsx: $("#fmt-xlsx").checked,
          }),
        });
        if (!res.ok) {
          const j = await res.json().catch(() => ({}));
          let msg = "Could not start job.";
          if (typeof j.detail === "string") msg = j.detail;
          else if (Array.isArray(j.detail))
            msg = j.detail.map((d) => d.msg || JSON.stringify(d)).join("; ");
          err.textContent = msg;
          err.classList.remove("hidden");
          return;
        }
        const run = await res.json();
        activeRunId = run.id;
        tablePage = 1;
        lastRunSnapshot = run;
        renderRun(run);
        $("#results-activity").classList.remove("hidden");
        $("#table-body").innerHTML = "";
        $("#pagination").classList.add("hidden");
        startPoll();
        await loadResultsTable();
      } catch (ex) {
        console.error(ex);
        err.textContent = `Cannot reach the API at ${API}. Start the server with: uvicorn src.web.app:app --host 127.0.0.1 --port 8000 and open this page from that address (not as a local file).`;
        err.classList.remove("hidden");
      } finally {
        startBtn.disabled = false;
      }
    });

    $("#btn-reset").addEventListener("click", resetForm);

    $("#btn-apply-filters").addEventListener("click", () => {
      tablePage = 1;
      loadResultsTable();
    });

    $$(".th-sort-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const key = btn.getAttribute("data-sort");
        if (!SORTABLE_RESULT_COLUMNS.has(key)) return;
        if (tableSort.key === key) {
          tableSort.order = tableSort.order === "asc" ? "desc" : "asc";
        } else {
          tableSort.key = key;
          tableSort.order = "asc";
        }
        syncSortHeaderState();
        tablePage = 1;
        loadResultsTable();
      });
    });
    normalizeTableSort();
    syncSortHeaderState();
    setupPerPageCustomSelect();
    setupWebsiteFilterSelect();
    setupHistoryBulkActions();
    setupResultsRowSelection();

    init();
  }

  function init() {
    if (window.location.protocol === "file:") {
      const tip = document.createElement("div");
      tip.className = "alert alert-error";
      tip.style.margin = "1rem";
      tip.innerHTML =
        "Open the dashboard in the browser at <strong>http://127.0.0.1:8000/</strong> after starting <code>uvicorn src.web.app:app --host 127.0.0.1 --port 8000</code>. " +
        "Opening <code>index.html</code> as a file will not load the API.";
      document.body.prepend(tip);
    }
    $("#status-label").className = "status-pill status-idle";
    $("#status-label").textContent = "Idle";
    $("#results-activity").classList.add("hidden");
    $("#results-empty").classList.remove("hidden");
    loadHistory();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupDashboard);
  } else {
    setupDashboard();
  }
})();
