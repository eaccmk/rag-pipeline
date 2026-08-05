class ThemeManager {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'dark';
        this.applyTheme(this.currentTheme);
        this.setupToggle();
    }

    applyTheme(theme) {
        const body = document.body;
        if (theme === 'light') {
            body.classList.add('light-mode');
        } else {
            body.classList.remove('light-mode');
        }
        localStorage.setItem('theme', theme);
    }

    toggle() {
        this.currentTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(this.currentTheme);
    }

    setupToggle() {
        const btn = document.getElementById('theme-toggle-btn');
        if (btn) {
            btn.addEventListener('click', () => this.toggle());
        }
    }
}

class UIStateManager {
    constructor() {
        this.currentQuery = null;
        this.isLoading = false;
    }

    setLoading(loading) {
        this.isLoading = loading;
        const btn = document.getElementById('btn-submit-query');
        const resultsSection = document.getElementById('results-section');
        const loadingIndicator = document.getElementById('loading-indicator');

        if (loading) {
            if (btn) {
                btn.disabled = true;
                const btnText = btn.querySelector('.btn-text');
                if (btnText) btnText.textContent = 'Analyzing RAG Pipeline...';
            }
            if (resultsSection) resultsSection.classList.add('hidden');
            if (loadingIndicator) {
                loadingIndicator.classList.remove('hidden');
                loadingIndicator.scrollIntoView({ behavior: 'smooth' });
            }
        } else {
            if (btn) {
                btn.disabled = false;
                const btnText = btn.querySelector('.btn-text');
                if (btnText) btnText.textContent = 'Analyze & Advise';
            }
            if (loadingIndicator) loadingIndicator.classList.add('hidden');
        }
    }

    displayNewQuery(query) {
        this.currentQuery = query;
        const queryDisplay = document.getElementById('current-query-display');
        if (queryDisplay) {
            queryDisplay.textContent = `Current Analysis: "${query}"`;
            queryDisplay.classList.remove('hidden');
        }
        this.setLoading(true);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const themeManager = new ThemeManager();
    const uiState = new UIStateManager();

    // Navigation Tabs
    const navItems = document.querySelectorAll('.nav-item');
    const tabContents = document.querySelectorAll('.tab-content');
    const pageTitle = document.getElementById('page-title');

    const titles = {
        'advisor': 'RAG pipeline for SMB Merchants',
        'signals': 'RBA & Market Signals Dashboard',
        'comparison': 'Guardrails Before/After Impact',
        'audit': 'JSON Decision Audit Log',
        'config': 'System Configuration'
    };

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetTab = item.getAttribute('data-tab');

            navItems.forEach(n => n.classList.remove('active'));
            tabContents.forEach(t => t.classList.remove('active'));

            item.classList.add('active');
            const targetEl = document.getElementById(`tab-${targetTab}`);
            if (targetEl) targetEl.classList.add('active');
            pageTitle.textContent = titles[targetTab] || 'RAG pipeline for SMB Merchants';

            if (targetTab === 'audit') {
                fetchAuditLogs();
            } else if (targetTab === 'signals') {
                fetchMarketData();
            } else if (targetTab === 'config') {
                fetchConfig();
            }
        });
    });

    // Customer Profiles Data for instant UI update
    const customerProfiles = {
        'CUST_001': {
            name: 'ABC Manufacturing Pty Ltd',
            loan: 'AUD $250,000 @ 4.8% (Var)',
            payment: 'AUD $4,500',
            term: '60 Months',
            risk: 'Low Risk',
            riskClass: 'tag-low'
        },
        'CUST_002': {
            name: 'Fresh Start Bakery',
            loan: 'AUD $50,000 @ 4.2% (Var)',
            payment: 'AUD $950',
            term: '36 Months',
            risk: 'Very Low Risk',
            riskClass: 'tag-low'
        },
        'CUST_003': {
            name: 'Heavy Haulage Pty Ltd',
            loan: 'AUD $1,850,000 @ 5.9% (Var)',
            payment: 'AUD $28,000',
            term: '120 Months',
            risk: 'High Risk',
            riskClass: 'tag-high'
        }
    };

    const customerSelect = document.getElementById('customer-selector');
    if (customerSelect) {
        customerSelect.addEventListener('change', (e) => {
            const custId = e.target.value;
            const profile = customerProfiles[custId];
            if (profile) {
                document.getElementById('cust-name').textContent = profile.name;
                document.getElementById('cust-loan').textContent = profile.loan;
                document.getElementById('cust-payment').textContent = profile.payment;
                document.getElementById('cust-term').textContent = profile.term;
                const riskEl = document.getElementById('cust-risk');
                if (riskEl) {
                    riskEl.textContent = profile.risk;
                    riskEl.className = `val ${profile.riskClass}`;
                }
            }
        });
    }

    // Preset Query Pills & Input Handler
    const presetBtns = document.querySelectorAll('.preset-btn');
    const queryInput = document.getElementById('query-input');
    const submitBtn = document.getElementById('btn-submit-query');

    if (queryInput && submitBtn) {
        queryInput.addEventListener('input', () => {
            submitBtn.disabled = queryInput.value.trim() === '';
        });
    }

    presetBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            if (queryInput) {
                queryInput.value = btn.textContent;
                if (submitBtn) submitBtn.disabled = false;
            }
        });
    });

    // Manual Refresh Button for Ollama Connection (Heartbeat)
    const refreshBtn = document.getElementById('btn-refresh-ollama');
    const refreshIcon = document.getElementById('refresh-icon');

    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            if (refreshIcon) refreshIcon.classList.add('spinning');
            await updateOllamaHealth();
            setTimeout(() => {
                if (refreshIcon) refreshIcon.classList.remove('spinning');
            }, 600);
        });
    }

    // Submit Query
    submitBtn.addEventListener('click', async () => {
        const queryText = queryInput.value.trim();
        if (!queryText) return;

        const selectedCustId = customerSelect ? customerSelect.value : 'CUST_001';
        const n8nToggle = document.getElementById('toggle-n8n-pipeline');
        const useN8n = localStorage.getItem('use_n8n_pipeline') === 'true' || (n8nToggle ? n8nToggle.checked : false);

        uiState.displayNewQuery(queryText);

        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: queryText,
                    customer_id: selectedCustId,
                    use_n8n: useN8n
                })
            });

            const data = await response.json();
            renderResults(data);

        } catch (err) {
            console.error('Error querying advisor:', err);
            uiState.setLoading(false);
        }
    });

    function renderResults(data) {
        uiState.setLoading(false);
        const loadingIndicator = document.getElementById('loading-indicator');
        const resultsSection = document.getElementById('results-section');

        if (loadingIndicator) loadingIndicator.classList.add('hidden');
        if (resultsSection) resultsSection.classList.remove('hidden');

        // Status & Confidence
        const statusBadge = document.getElementById('status-badge');
        const statusText = document.getElementById('status-text');
        const confidenceVal = document.getElementById('confidence-val');
        const answerText = document.getElementById('advisor-answer-text');

        if (data.is_valid) {
            statusBadge.className = 'status-badge';
            statusText.textContent = '✓ SAFE TO DEPLOY';
        } else {
            statusBadge.className = 'status-badge failed';
            statusText.textContent = 'NOT ❌ SAFE TO DEPLOY';
        }

        confidenceVal.textContent = data.confidence.toFixed(2);
        answerText.innerHTML = renderMarkdownToHtml(data.answer);

        // Render RAG Citations as inline paragraph with hyperlinked text
        const citationsPara = document.getElementById('citations-para') || document.getElementById('citations-list');
        if (citationsPara && data.sources) {
            citationsPara.innerHTML = '';
            const linksHtml = data.sources.map(src => {
                const urlMatch = src.match(/\((https?:\/\/[^\)]+)\)/);
                if (urlMatch) {
                    const url = urlMatch[1];
                    const label = src.replace(/\(https?:\/\/[^\)]+\)/, '').trim();
                    return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="citation-link">${label}</a>`;
                } else {
                    return `<span class="citation-text">${src}</span>`;
                }
            }).join(' <span class="citation-sep">•</span> ');

            citationsPara.innerHTML = linksHtml;
        }

        // Guardrails Check
        const factCheck = data.validation_results.fact_check;
        const confCheck = data.validation_results.confidence_check;
        const discCheck = data.validation_results.disclaimer_check;

        document.getElementById('fact-reason').textContent = factCheck.reason;
        document.getElementById('conf-reason').textContent = confCheck.reason;
        document.getElementById('disc-reason').textContent = discCheck.reason;

        setCheckStatus('check-fact', factCheck.pass);
        setCheckStatus('check-conf', confCheck.pass);
        setCheckStatus('check-disc', discCheck.pass);

        // Metrics
        const m = data.ragas_metrics;
        document.getElementById('m-context').textContent = m.context_relevance.toFixed(2);
        document.getElementById('m-answer').textContent = m.answer_relevance.toFixed(2);
        document.getElementById('m-faith').textContent = m.faithfulness.toFixed(2);
        document.getElementById('m-avg').textContent = m.average_score.toFixed(2);

        // Customer Scenario / Mock Badge Update
        const cdrBadge = document.getElementById('cdr-mode-badge');
        if (cdrBadge) {
            const isMock = data.is_mock !== undefined ? data.is_mock : true;
            cdrBadge.className = `mode-badge ${isMock ? 'mock' : 'real'}`;
            cdrBadge.textContent = isMock ? '[CUSTOMER SCENARIO]' : '[LIVE DATA]';
        }

        // Scroll to results smoothly
        if (resultsSection) resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    function setCheckStatus(elementId, isPassed) {
        const el = document.getElementById(elementId);
        if (!el) return;
        const icon = el.querySelector('.g-icon');
        if (isPassed) {
            el.classList.remove('fail');
            if (icon) icon.textContent = '✓';
        } else {
            el.classList.add('fail');
            if (icon) icon.textContent = '✗';
        }
    }

    // Health Check Polling
    async function updateOllamaHealth() {
        try {
            const res = await fetch('/api/health');
            const data = await res.json();

            const light = document.getElementById('status-light');
            const text = document.getElementById('ollama-status-sub');
            const modelName = document.getElementById('model-name');
            const connStatus = document.getElementById('ollama-connection-status');

            if (modelName) modelName.textContent = data.model || 'llama3.2:1b';
            if (light) light.className = `status-indicator ${data.status}`;
            if (text) {
                text.className = `status-sub ${data.status}`;
                if (data.status === 'available') {
                    text.textContent = 'Ready (Online)';
                } else if (data.status === 'unavailable') {
                    text.textContent = 'Offline - Check Ollama';
                } else {
                    text.textContent = 'Initializing...';
                }
            }

            // Sync Configuration Panel status badge
            if (connStatus) {
                const dot = connStatus.querySelector('.status-dot');
                const textEl = connStatus.querySelector('.status-text');
                if (dot) dot.className = `status-dot ${data.status}`;
                if (textEl) textEl.textContent = data.status === 'available' ? 'Available' : 'Unavailable';
            }
        } catch (e) {
            const light = document.getElementById('status-light');
            const text = document.getElementById('ollama-status-sub');
            const connStatus = document.getElementById('ollama-connection-status');
            if (light) light.className = 'status-indicator unavailable';
            if (text) {
                text.className = 'status-sub unavailable';
                text.textContent = 'Offline';
            }
            if (connStatus) {
                const dot = connStatus.querySelector('.status-dot');
                const textEl = connStatus.querySelector('.status-text');
                if (dot) dot.className = 'status-dot unavailable';
                if (textEl) textEl.textContent = 'Unavailable';
            }
        }
    }

    // Fetch System Config
    async function fetchConfig() {
        try {
            const res = await fetch('/api/config');
            const data = await res.json();

            const urlEl = document.getElementById('ollama-url');
            const modelEl = document.getElementById('ollama-model');
            const modeEl = document.getElementById('execution-mode');
            const dataModeEl = document.getElementById('data-mode');
            const logLevelEl = document.getElementById('log-level');
            const mockStatusEl = document.getElementById('mock-status');
            const n8nUrlEl = document.getElementById('n8n-url');
            const qdrantUrlEl = document.getElementById('qdrant-url');

            if (urlEl) urlEl.textContent = data.ollama_base_url || 'http://localhost:11434';
            if (modelEl) modelEl.textContent = data.ollama_model || 'llama3.2:1b';
            if (modeEl) modeEl.textContent = data.execution_mode || 'local';
            if (dataModeEl) dataModeEl.textContent = data.use_mock_data ? 'Mock Data' : 'Real APIs';
            if (logLevelEl) logLevelEl.textContent = data.log_level || 'INFO';

            if (n8nUrlEl) {
                n8nUrlEl.textContent = data.n8n_base_url || 'http://localhost:5678';
            }

            if (qdrantUrlEl) {
                const qdrantDashboardUrl = `http://${data.qdrant_host || 'localhost'}:${data.qdrant_port || 6333}/dashboard#/collections/${data.qdrant_collection || 'loan_advisor_rag'}`;
                qdrantUrlEl.textContent = `${qdrantDashboardUrl} (${data.qdrant_collection || 'loan_advisor_rag'})`;
            }

            if (mockStatusEl) {
                if (data.use_mock_data) {
                    mockStatusEl.className = 'mock-status-badge mock';
                    mockStatusEl.textContent = 'MOCK DATA';
                } else {
                    mockStatusEl.className = 'mock-status-badge';
                    mockStatusEl.textContent = 'REAL DATA';
                }
            }

            const n8nToggle = document.getElementById('toggle-n8n-pipeline');

            function updateN8nToggleUI(isChecked) {
                const badge = document.getElementById('n8n-status-badge');
                const msg = document.getElementById('n8n-status-msg');
                const cfgStatus = document.getElementById('n8n-pipeline-status');
                const detailsContainer = document.getElementById('n8n-details-container');

                if (isChecked) {
                    if (badge) {
                        badge.className = 'n8n-status-pill on';
                        badge.textContent = 'ON (Connected to n8n Webhook now)';
                    }
                    if (msg) {
                        msg.textContent = 'Connected to n8n Webhook now: http://localhost:5678/';
                        msg.style.color = 'var(--accent-green)';
                    }
                    if (cfgStatus) cfgStatus.textContent = 'ON (n8n Webhook Engine Active)';
                    if (detailsContainer) detailsContainer.classList.remove('hidden');
                } else {
                    if (badge) {
                        badge.className = 'n8n-status-pill off';
                        badge.textContent = 'OFF (Using Python Native RAG)';
                    }
                    if (msg) {
                        msg.textContent = 'Python Native RAG pipeline active (http://localhost:8000)';
                        msg.style.color = 'var(--text-muted)';
                    }
                    if (cfgStatus) cfgStatus.textContent = 'OFF (Python Native RAG)';
                    if (detailsContainer) detailsContainer.classList.add('hidden');
                }
            }

            if (n8nToggle) {
                const savedState = localStorage.getItem('use_n8n_pipeline');
                if (savedState !== null) {
                    n8nToggle.checked = savedState === 'true';
                } else {
                    n8nToggle.checked = typeof data.use_n8n_pipeline === 'boolean' ? data.use_n8n_pipeline : false;
                }
                updateN8nToggleUI(n8nToggle.checked);

                n8nToggle.addEventListener('change', () => {
                    const isChecked = n8nToggle.checked;
                    updateN8nToggleUI(isChecked);
                    localStorage.setItem('use_n8n_pipeline', isChecked);

                    fetch('/api/config', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ use_n8n_pipeline: isChecked })
                    }).catch(err => console.error('Error saving n8n config state:', err));
                });
            }


            const cdrBadge = document.getElementById('cdr-mode-badge');
            if (cdrBadge) {
                const isMock = data.use_mock_data;
                cdrBadge.className = `mode-badge ${isMock ? 'mock' : 'real'}`;
                cdrBadge.textContent = isMock ? '[CUSTOMER SCENARIO]' : '[LIVE DATA]';
            }

            // Sync Ollama status for Config panel
            await updateOllamaHealth();
        } catch (e) {
            console.error('Error fetching config:', e);
        }
    }

    // Fetch Stats on load

    async function fetchStats() {
        try {
            const res = await fetch('/api/stats');
            const data = await res.json();
            document.getElementById('hdr-cash-rate').textContent = `${data.rba_cash_rate}%`;
            document.getElementById('hdr-pass-rate').textContent = `${data.pass_rate}%`;
        } catch (e) {
            console.log('Stats endpoint offline or starting up.');
        }
    }

    // Fetch Audit Logs
    async function fetchAuditLogs() {
        try {
            const res = await fetch('/api/alerts');
            const data = await res.json();
            const tbody = document.getElementById('audit-table-body');
            tbody.innerHTML = '';

            if (!data.alerts || data.alerts.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No decision logs recorded yet. Run a query!</td></tr>';
                return;
            }

            data.alerts.reverse().forEach(log => {
                const tr = document.createElement('tr');
                const timeStr = new Date(log.timestamp).toLocaleTimeString();
                const statusHtml = log.status === 'PASSED'
                    ? '<span style="color: var(--accent-green); font-weight:700;">PASSED</span>'
                    : '<span style="color: var(--accent-red); font-weight:700;">BLOCKED</span>';

                tr.innerHTML = `
                    <td>${timeStr}</td>
                    <td>${log.query}</td>
                    <td>${log.validation?.confidence_check?.confidence_score || '0.85'}</td>
                    <td>Fact: ${log.validation?.fact_check?.pass ? '✓' : '✗'}, Disc: ${log.validation?.disclaimer_check?.pass ? '✓' : '✗'}</td>
                    <td>${statusHtml}</td>
                `;
                tbody.appendChild(tr);
            });
        } catch (e) {
            console.error('Error fetching audit logs:', e);
        }
    }

    async function fetchMarketData() {
        try {
            const res = await fetch('/api/market_data');
            const data = await res.json();
            const stanceChip = document.getElementById('rba-stance-chip');
            if (data.rba) {
                const rba = data.rba;
                if (stanceChip) stanceChip.textContent = `RBA Stance: ${rba.rba_stance.toUpperCase()}`;

                const cashEl = document.getElementById('rba-card-cash');
                const cpiEl = document.getElementById('rba-card-cpi');
                const forecastEl = document.getElementById('rba-card-forecast');
                const cutProbEl = document.getElementById('rba-card-cut-prob');
                const stanceBadgeEl = document.getElementById('rba-stance-badge');
                const formulaSubEl = document.getElementById('rba-formula-sub');

                const cashRate = rba.official_cash_rate || 4.35;
                const cpiRate = rba.current_inflation_rate || 3.2;
                const forecastRate = rba.rate_expectations_12m?.expected_rate || 3.85;
                const cutCount = Math.max(1, Math.round((cashRate - forecastRate) / 0.25));

                if (cashEl) cashEl.textContent = `${cashRate.toFixed(2)}%`;
                if (cpiEl) cpiEl.textContent = `${cpiRate.toFixed(1)}%`;
                if (forecastEl) forecastEl.textContent = `${forecastRate.toFixed(2)}%`;
                if (cutProbEl) cutProbEl.textContent = `58%`;
                if (stanceBadgeEl) stanceBadgeEl.textContent = `RBA Stance: ${rba.rba_stance.toUpperCase()}`;

                if (formulaSubEl) {
                    formulaSubEl.innerHTML = `Formula: <span class="num-highlight">${cashRate.toFixed(2)}%</span> Cash Rate - (<span class="num-highlight">${cutCount}</span> × <span class="num-highlight">0.25%</span> Cuts) = <span class="num-highlight">${forecastRate.toFixed(2)}%</span>`;
                }
            }


        } catch (e) {
            console.error('Error fetching market data:', e);
        }
    }

    // Initializations
    fetchStats();
    fetchConfig();
    updateOllamaHealth();
    setInterval(updateOllamaHealth, 30000);
});

function renderMarkdownToHtml(md) {
    if (!md) return '';
    // Strip trailing Confidence lines
    let text = md.replace(/Confidence:\s*\d+(\.\d+)?/gi, '').trim();

    const lines = text.split('\n');
    let htmlLines = [];
    let inTable = false;
    let tableHeader = [];
    let tableRows = [];

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i].trim();

        if (line.startsWith('|') && line.endsWith('|')) {
            const cells = line.split('|').map(c => c.trim()).slice(1, -1);
            if (cells.length > 0 && cells.every(c => /^:?-+:?$/.test(c))) {
                continue; // table header divider line
            }
            if (!inTable) {
                inTable = true;
                tableHeader = cells;
            } else {
                tableRows.push(cells);
            }
            continue;
        } else if (inTable) {
            htmlLines.push(buildHtmlTable(tableHeader, tableRows));
            inTable = false;
            tableHeader = [];
            tableRows = [];
        }

        if (line.startsWith('>')) {
            const quoteText = formatInlineMarkdown(line.replace(/^>\s*/, ''));
            htmlLines.push(`<blockquote class="guidance-disclaimer">${quoteText}</blockquote>`);
        } else if (line.toLowerCase().startsWith('disclaimer:')) {
            const quoteText = formatInlineMarkdown(line);
            htmlLines.push(`<blockquote class="guidance-disclaimer">${quoteText}</blockquote>`);
        } else if (line.length > 0) {
            htmlLines.push(`<p>${formatInlineMarkdown(line)}</p>`);
        }
    }

    if (inTable) {
        htmlLines.push(buildHtmlTable(tableHeader, tableRows));
    }

    return htmlLines.join('');
}

function buildHtmlTable(header, rows) {
    let ths = header.map(h => `<th>${formatInlineMarkdown(h)}</th>`).join('');
    let trs = rows.map(r => `<tr>${r.map(c => `<td>${formatInlineMarkdown(c)}</td>`).join('')}</tr>`).join('');
    return `<div class="table-responsive"><table class="guidance-table"><thead><tr>${ths}</tr></thead><tbody>${trs}</tbody></table></div>`;
}

function formatInlineMarkdown(str) {
    if (!str) return '';
    let s = str.replace(/\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="guidance-link">$1 &rarr;</a>');
    s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    return s;
}

// Clipboard Copy Event Listener
document.addEventListener('click', (e) => {
    const btn = e.target.closest('.copy-btn');
    if (!btn) return;

    const targetId = btn.getAttribute('data-copy-target');
    let textToCopy = '';

    if (targetId) {
        const targetEl = document.getElementById(targetId);
        if (targetEl) {
            textToCopy = targetEl.textContent.trim();
        }
    }

    if (!textToCopy && btn.getAttribute('data-copy-value')) {
        textToCopy = btn.getAttribute('data-copy-value');
    }

    if (textToCopy) {
        // Smart URL extraction if embedded in string like "Connected to n8n Webhook now: http://localhost:5678/"
        const urlMatch = textToCopy.match(/(https?:\/\/[^\s()]+)/);
        if (urlMatch) {
            textToCopy = urlMatch[1];
        } else {
            // Strip trailing parenthetical labels like "(loan_advisor_rag)" or "(Ollama)"
            textToCopy = textToCopy.replace(/\s*\([^)]*\)\s*$/, '').trim();
        }

        navigator.clipboard.writeText(textToCopy).then(() => {
            const icon = btn.querySelector('i');
            if (icon) {
                icon.className = 'fa-solid fa-check';
                btn.classList.add('copied');
                setTimeout(() => {
                    icon.className = 'fa-solid fa-copy';
                    btn.classList.remove('copied');
                }, 1500);

            }
        }).catch(err => {
            console.error('Failed to copy to clipboard:', err);
        });
    }
});

