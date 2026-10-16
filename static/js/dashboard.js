/**
 * Dashboard: AJAX scan, website analyzer, chart, live stats update
 */
(function () {
    const form = document.getElementById("scanForm");
    const websiteForm = document.getElementById("websiteForm");
    const scanBtn = document.getElementById("scanBtn");
    const resultEl = document.getElementById("scanResult");
    const chartCanvas = document.getElementById("statsChart");

    let chart = null;

    function initChart() {
        if (!chartCanvas) return;

        const safe = parseInt(chartCanvas.dataset.safe, 10) || 0;
        const suspicious = parseInt(chartCanvas.dataset.suspicious, 10) || 0;
        const dangerous = parseInt(chartCanvas.dataset.dangerous, 10) || 0;

        chart = new Chart(chartCanvas, {
            type: "doughnut",
            data: {
                labels: ["Safe", "Suspicious", "Dangerous"],
                datasets: [{
                    data: [safe, suspicious, dangerous],
                    backgroundColor: ["#22c55e", "#eab308", "#ef4444"],
                    borderWidth: 0,
                    hoverOffset: 6,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { color: "#94a3b8", padding: 14, boxWidth: 12 },
                    },
                },
                cutout: "65%",
            },
        });
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    function formatThreatLevel(level) {
        const value = (level || "suspicious").toLowerCase();
        return value.charAt(0).toUpperCase() + value.slice(1);
    }

    function threatRow(level) {
        const text = formatThreatLevel(level);
        return `<span class="threat-dot threat-${level}"></span>${escapeHtml(text)}`;
    }

    function setLoading(loading) {
        if (!scanBtn) return;
        scanBtn.disabled = loading;
        scanBtn.querySelector(".btn-text")?.classList.toggle("d-none", loading);
        scanBtn.querySelector(".btn-loading")?.classList.toggle("d-none", !loading);
    }

    function setWebsiteLoading(loading) {
        const btn = document.getElementById("websiteBtn");
        if (!btn) return;
        btn.disabled = loading;
        btn.querySelector(".btn-text")?.classList.toggle("d-none", loading);
        btn.querySelector(".btn-loading")?.classList.toggle("d-none", !loading);
    }

    function renderResult(result) {
        if (!resultEl) return;
        const threat = result.threat || {};
        const level = result.threat_level || "suspicious";
        const color = threat.color || "warning";

        resultEl.classList.remove("d-none");
        resultEl.innerHTML = `
            <div class="result-panel threat-${level}">
                <div class="threat-level-hero">
                    <span class="threat-badge badge-${color} threat-level-badge">
                        <i class="fa-solid ${threat.icon || "fa-shield"}"></i>
                        ${escapeHtml(threat.text || formatThreatLevel(level))}
                    </span>
                    <p class="threat-level-sub text-muted mb-0">${escapeHtml(result.type || "")} scan</p>
                </div>
                <h3 class="result-label">${escapeHtml(result.label || "")}</h3>
                <p class="result-action mb-0">${escapeHtml(threat.action || "Review this content before acting.")}</p>
            </div>`;
    }

    function renderWebsiteResult(result) {
        const websiteEl = document.getElementById("websiteResult");
        if (!websiteEl) return;

        const threat = result.threat || {};
        const overall = result.overall || {};
        const summary = result.link_summary || {};
        const level = overall.threat_level || result.threat_level || "suspicious";
        const color = threat.color || "warning";
        const links = (result.links || []).slice(0, 12);

        websiteEl.classList.remove("d-none");
        websiteEl.innerHTML = `
            <div class="result-panel threat-${level} website-report">
                <div class="threat-level-hero">
                    <span class="threat-badge badge-${color} threat-level-badge">
                        <i class="fa-solid ${threat.icon || "fa-shield"}"></i>
                        ${escapeHtml(threat.text || formatThreatLevel(level))}
                    </span>
                    <p class="threat-level-sub text-muted mb-0">Website analysis</p>
                </div>
                <p class="small text-muted mb-3">${escapeHtml(result.seed_url || "")}</p>
                <div class="link-stats-grid">
                    <div><strong>${summary.total_hyperlinks || 0}</strong><span>Links</span></div>
                    <div class="text-success"><strong>${summary.safe_hyperlinks || 0}</strong><span>Safe</span></div>
                    <div class="text-warning"><strong>${summary.suspicious_hyperlinks || 0}</strong><span>Suspicious</span></div>
                    <div class="text-danger"><strong>${summary.phishing_hyperlinks || 0}</strong><span>Phishing</span></div>
                </div>
                ${links.length ? `
                <div class="table-responsive mt-3">
                    <table class="table table-dark table-sm mb-0">
                        <thead><tr><th>URL</th><th>Threat</th></tr></thead>
                        <tbody>
                            ${links.map((link) => `
                                <tr>
                                    <td class="small" title="${escapeHtml(link.url)}">${escapeHtml(link.url.length > 52 ? link.url.slice(0, 52) + "…" : link.url)}</td>
                                    <td>${threatRow(link.threat_level)}</td>
                                </tr>`).join("")}
                        </tbody>
                    </table>
                </div>` : ""}
            </div>`;
    }

    function updateStats(stats) {
        if (!stats) return;
        document.getElementById("statTotal").textContent = stats.total;
        document.getElementById("statSafe").textContent = stats.safe;
        document.getElementById("statThreats").textContent = stats.threats;
        document.getElementById("statDangerous").textContent = stats.dangerous;

        if (chart) {
            chart.data.datasets[0].data = [stats.safe, stats.suspicious, stats.dangerous];
            chart.update();
        }
    }

    function prependHistory(scan) {
        const tbody = document.getElementById("historyBody");
        const empty = document.getElementById("emptyHistory");
        if (empty) empty.remove();

        const tr = document.createElement("tr");
        const input = scan.input_text.length > 60
            ? scan.input_text.slice(0, 60) + "…"
            : scan.input_text;

        tr.innerHTML = `
            <td class="input-cell" title="${escapeHtml(scan.input_text)}">${escapeHtml(input)}</td>
            <td><span class="badge bg-secondary">${escapeHtml(scan.input_type)}</span></td>
            <td>${escapeHtml(scan.label)}</td>
            <td>${threatRow(scan.threat_level)}</td>
            <td class="text-muted small">Just now</td>`;
        tbody.prepend(tr);

        while (tbody.rows.length > 10) {
            tbody.deleteRow(-1);
        }
    }

    form?.addEventListener("submit", async function (e) {
        e.preventDefault();
        const input = document.getElementById("input_data");
        const value = input?.value?.trim();
        if (!value) return;

        setLoading(true);

        try {
            const res = await fetch(form.action, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                },
                credentials: "same-origin",
                body: JSON.stringify({ input_data: value }),
            });

            const raw = await res.text();
            let data = {};
            try {
                data = raw ? JSON.parse(raw) : {};
            } catch {
                alert(
                    res.status === 401
                        ? "Please log in again."
                        : "Server returned an invalid response (" + res.status + ")."
                );
                return;
            }

            if (!res.ok || !data.ok) {
                const errorMsg = data.error || data.message || "Scan failed.";
                if (resultEl) {
                    resultEl.classList.remove("d-none");
                    resultEl.innerHTML = `
                        <div class="alert alert-danger border-0 shadow-sm d-flex align-items-start gap-2 mt-3" style="background: rgba(239, 68, 68, 0.12); color: #fca5a5; border-left: 4px solid #ef4444 !important; border-radius: 8px; padding: 1rem;">
                            <i class="fa-solid fa-circle-exclamation mt-1"></i>
                            <div><strong>Scan Notice:</strong> ${escapeHtml(errorMsg)}</div>
                        </div>`;
                } else {
                    alert(errorMsg);
                }
                return;
            }

            renderResult(data.result);
            if (data.stats) updateStats(data.stats);
            if (data.scan) prependHistory(data.scan);
        } catch (err) {
            const errorMsg = "Network error. Could not reach the server" + (err && err.message ? " (" + err.message + ")" : "") + ".";
            if (resultEl) {
                resultEl.classList.remove("d-none");
                resultEl.innerHTML = `
                    <div class="alert alert-danger border-0 shadow-sm d-flex align-items-start gap-2 mt-3" style="background: rgba(239, 68, 68, 0.12); color: #fca5a5; border-left: 4px solid #ef4444 !important; border-radius: 8px; padding: 1rem;">
                        <i class="fa-solid fa-circle-exclamation mt-1"></i>
                        <div><strong>Network Error:</strong> ${escapeHtml(errorMsg)}</div>
                    </div>`;
            } else {
                alert(errorMsg);
            }
        } finally {
            setLoading(false);
        }
    });

    function normalizeWebsiteUrl(raw) {
        let value = (raw || "").trim();
        if (!value) return "";
        // Accept bare domains (e.g. stackoverflow.com) and protocol-relative URLs.
        if (value.startsWith("//")) {
            value = "https:" + value;
        } else if (!/^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//.test(value)) {
            value = "https://" + value;
        }
        return value;
    }

    websiteForm?.addEventListener("submit", async function (e) {
        e.preventDefault();
        const input = document.getElementById("website_url");
        const value = normalizeWebsiteUrl(input?.value);
        if (!value) {
            alert("Website URL is required.");
            return;
        }
        if (input) input.value = value;

        setWebsiteLoading(true);

        try {
            const res = await fetch(websiteForm.action, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                },
                credentials: "same-origin",
                body: JSON.stringify({ url: value }),
            });

            const raw = await res.text();
            let data = {};
            try {
                data = raw ? JSON.parse(raw) : {};
            } catch {
                alert(
                    res.status === 401
                        ? "Please log in again."
                        : "Server returned an invalid response (" + res.status + ")."
                );
                return;
            }

            if (!res.ok || !data.ok) {
                const errorMsg = data.error || data.message || "Website analysis failed.";
                const websiteEl = document.getElementById("websiteResult");
                if (websiteEl) {
                    websiteEl.classList.remove("d-none");
                    websiteEl.innerHTML = `
                        <div class="alert alert-warning border-0 shadow-sm d-flex align-items-start gap-2 mt-3" style="background: rgba(234, 179, 8, 0.12); color: #fde047; border-left: 4px solid #eab308 !important; border-radius: 8px; padding: 1rem;">
                            <i class="fa-solid fa-triangle-exclamation mt-1"></i>
                            <div><strong>Crawler Notice:</strong> ${escapeHtml(errorMsg)}</div>
                        </div>`;
                } else {
                    alert(errorMsg);
                }
                return;
            }

            renderWebsiteResult(data.result);
            if (data.stats) updateStats(data.stats);
            if (data.result) {
                prependHistory({
                    input_text: data.result.seed_url || value,
                    input_type: "WEBSITE",
                    label: data.result.seed_analysis?.label || "Website analysis",
                    threat_level: data.result.threat_level || "suspicious",
                });
            }
        } catch (err) {
            alert(
                "Network error. Could not reach the server" +
                    (err && err.message ? " (" + err.message + ")" : "") +
                    "."
            );
        } finally {
            setWebsiteLoading(false);
        }
    });

    initChart();
})();
