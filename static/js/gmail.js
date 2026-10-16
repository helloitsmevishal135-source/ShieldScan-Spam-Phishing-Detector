/**
 * Gmail dashboard: poll for new scan results and optional disconnect AJAX
 */
(function () {
    const actions = document.getElementById("gmailActions");
    if (!actions) return;

    const connected = actions.dataset.connected === "true";
    const syncMinutes = parseInt(actions.dataset.syncMinutes, 10) || 5;
    const pollMs = Math.max(syncMinutes, 1) * 60 * 1000;
    const tbody = document.getElementById("gmailEmailBody");

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str || "";
        return div.innerHTML;
    }

    function truncate(str, len) {
        if (!str) return "";
        return str.length > len ? str.slice(0, len) + "…" : str;
    }

    function formatTime(iso) {
        if (!iso) return "";
        try {
            const d = new Date(iso);
            return d.toLocaleString(undefined, {
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
            });
        } catch {
            return "";
        }
    }

    function renderEmailRows(emails) {
        if (!tbody || !emails) return;

        if (!emails.length) return;

        const empty = document.getElementById("emptyGmailEmails");
        if (empty) empty.remove();

        tbody.innerHTML = emails
            .map(
                (e) => {
                    const level = (e.threat_level || "suspicious").toLowerCase();
                    const levelText = level.charAt(0).toUpperCase() + level.slice(1);
                    return `
            <tr class="email-row email-${escapeHtml(e.risk_label)}">
                <td class="input-cell" title="${escapeHtml(e.subject)}">${escapeHtml(truncate(e.subject, 50))}</td>
                <td class="small text-muted">${escapeHtml(truncate(e.sender, 40))}</td>
                <td><span class="threat-dot threat-${escapeHtml(level)}"></span>${escapeHtml(levelText)}</td>
                <td class="small">${escapeHtml(e.label || "")}</td>
                <td class="text-muted small">${escapeHtml(formatTime(e.created_at))}</td>
            </tr>`;
                }
            )
            .join("");
    }

    async function refreshEmails() {
        try {
            const res = await fetch("/gmail/emails", {
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });
            const data = await res.json();
            if (data.ok && data.emails) {
                renderEmailRows(data.emails);
            }
        } catch {
            /* ignore polling errors */
        }
    }

    async function refreshStatus() {
        try {
            const res = await fetch("/gmail/status", {
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });
            const data = await res.json();
            const el = document.getElementById("gmailLastSync");
            if (el && data.last_sync) {
                el.textContent = "Last sync: " + formatTime(data.last_sync);
            }
        } catch {
            /* ignore */
        }
    }

    function setRefreshLoading(loading) {
        const btn = document.getElementById("gmailRefreshBtn");
        if (!btn) return;
        btn.disabled = loading;
        btn.querySelector(".btn-text")?.classList.toggle("d-none", loading);
        btn.querySelector(".btn-loading")?.classList.toggle("d-none", !loading);
    }

    function showRefreshStatus(message, kind) {
        const el = document.getElementById("gmailRefreshStatus");
        if (!el) return;
        el.className = "w-100 small mt-1 text-" + (kind || "muted");
        el.textContent = message || "";
    }

    document.getElementById("gmailDisconnectForm")?.addEventListener("submit", async function (e) {
        e.preventDefault();
        if (!confirm("Disconnect Gmail? Automated scanning will stop.")) return;
        try {
            await fetch(this.action, {
                method: "POST",
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });
            window.location.reload();
        } catch {
            this.submit();
        }
    });

    document.getElementById("gmailRefreshBtn")?.addEventListener("click", async function () {
        const url = this.dataset.syncUrl || "/gmail/sync";
        setRefreshLoading(true);
        showRefreshStatus("Refreshing Gmail…", "muted");
        try {
            const res = await fetch(url, {
                method: "POST",
                headers: { "X-Requested-With": "XMLHttpRequest" },
                credentials: "same-origin",
            });
            const raw = await res.text();
            let data = {};
            try {
                data = raw ? JSON.parse(raw) : {};
            } catch {
                showRefreshStatus(
                    res.status === 401
                        ? "Please log in again."
                        : "Server returned an invalid response (" + res.status + ").",
                    "danger"
                );
                return;
            }
            if (!res.ok || data.success === false || data.ok === false) {
                showRefreshStatus(
                    data.message || data.error || "Gmail refresh failed. Please try again.",
                    "danger"
                );
                return;
            }
            if (data.emails) {
                renderEmailRows(data.emails);
            } else {
                await refreshEmails();
            }
            const lastSyncEl = document.getElementById("gmailLastSync");
            if (lastSyncEl && data.last_sync) {
                lastSyncEl.classList.remove("d-none");
                lastSyncEl.textContent = "Last sync: " + formatTime(data.last_sync);
            } else {
                await refreshStatus();
            }
            showRefreshStatus(data.message || "Gmail refreshed.", "success");
        } catch (err) {
            showRefreshStatus(
                "Network error. Could not reach the server" +
                    (err && err.message ? " (" + err.message + ")" : "") +
                    ".",
                "danger"
            );
        } finally {
            setRefreshLoading(false);
        }
    });

    if (connected) {
        setInterval(refreshEmails, pollMs);
        setInterval(refreshStatus, pollMs);
    }
})();
