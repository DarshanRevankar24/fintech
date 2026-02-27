// DOM Elements
const tbody = document.getElementById('portfolio-body');
const addRowBtn = document.getElementById('add-row-btn');
const analyzeBtn = document.getElementById('analyze-btn');

// Sections
const sectionUpload = document.getElementById('upload-section');
const sectionLoading = document.getElementById('loading-section');
const sectionResult = document.getElementById('result-section');

// Loading Elements
const loadingText = document.getElementById('loading-text');
const progressBar = document.getElementById('progress-bar');

// Initialize with one empty row
document.addEventListener('DOMContentLoaded', () => {
    addRow();
    // Enable analyze button by default now
    analyzeBtn.disabled = false;
});

// Dynamic Table Logic
addRowBtn.addEventListener('click', addRow);

function addRow() {
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td><input type="text" class="table-input ticker-input" placeholder="e.g. AAPL" required></td>
        <td><input type="number" step="any" min="0.01" class="table-input shares-input" placeholder="10" required></td>
        <td><input type="number" step="any" min="0.01" class="table-input price-input" placeholder="150.00" required></td>
        <td><input type="date" class="table-input date-input" required></td>
        <td>
            <button class="btn-icon delete-row-btn" title="Remove row">
                <i class="fa-solid fa-trash"></i>
            </button>
        </td>
    `;
    tbody.appendChild(tr);

    // Delete row event
    tr.querySelector('.delete-row-btn').addEventListener('click', () => {
        if (tbody.querySelectorAll('tr').length > 1) {
            tr.remove();
        } else {
            alert("You must have at least one holding in your portfolio.");
        }
    });
}

function gatherPortfolioData() {
    const holdings = [];
    const rows = tbody.querySelectorAll('tr');

    for (const row of rows) {
        const ticker = row.querySelector('.ticker-input').value.trim();
        const shares = parseFloat(row.querySelector('.shares-input').value);
        const purchasePrice = parseFloat(row.querySelector('.price-input').value);
        const purchaseDate = row.querySelector('.date-input').value;

        if (!ticker || isNaN(shares) || isNaN(purchasePrice) || !purchaseDate) {
            throw new Error("Please fill out all fields for every row.");
        }

        holdings.push({
            ticker: ticker,
            shares: shares,
            purchase_price: purchasePrice,
            purchase_date: purchaseDate,
            current_price: null // Let the backend fetch it
        });
    }

    return holdings;
}

// Analyze Process flow
analyzeBtn.addEventListener('click', async () => {
    // Switch to loading UI
    sectionUpload.classList.add('hidden');
    sectionLoading.classList.remove('hidden');

    try {
        // Step 1: Gather Manual Data
        let parsedHoldings = [];
        try {
            parsedHoldings = gatherPortfolioData();
        } catch (e) {
            // Revert UI immediately if validation fails
            sectionLoading.classList.add('hidden');
            sectionUpload.classList.remove('hidden');
            alert(e.message);
            return;
        }

        updateLoadingState(`Fetching real-time prices for ${parsedHoldings.length} assets...`, 30);

        // Step 2: Request Explanation
        const userLevel = document.getElementById('user-level').value;
        const includeTax = document.getElementById('include-tax').checked;
        const includeRebalance = document.getElementById('include-rebalance').checked;

        const explainReqPayload = {
            portfolio: parsedHoldings,
            user_level: userLevel,
            include_tax_analysis: includeTax,
            include_rebalancing: includeRebalance,
            transcript_context: null
        };

        const explainRes = await fetch('/api/explain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(explainReqPayload)
        });

        if (!explainRes.ok) {
            const errData = await explainRes.json();
            throw new Error(errData.detail || 'Failed to generate explanation');
        }

        const reportData = await explainRes.json();
        updateLoadingState("Finalizing report...", 100);

        // Wait a small moment for visuals
        setTimeout(() => {
            renderDashboard(reportData, includeTax, includeRebalance);
        }, 500);

    } catch (error) {
        alert("Error: " + error.message);
        // Revert UI
        sectionLoading.classList.add('hidden');
        analyzeBtn.disabled = false;
    }
});

function updateLoadingState(text, percent) {
    loadingText.textContent = text;
    progressBar.style.width = `${percent}%`;
}

// Render Dashboard
function renderDashboard(data, showTax, showRebalance) {
    sectionLoading.classList.add('hidden');
    sectionResult.classList.remove('hidden');

    const metrics = data.portfolio_metrics;

    // Top Stats
    document.getElementById('total-value').textContent = formatCurrency(metrics.total_value);

    const gainEl = document.getElementById('total-gain');
    gainEl.textContent = `${formatCurrency(metrics.unrealized_gain)} (${metrics.unrealized_gain_percent > 0 ? '+' : ''}${metrics.unrealized_gain_percent}%)`;
    if (metrics.unrealized_gain >= 0) {
        gainEl.className = 'gain-positive';
    } else {
        gainEl.className = 'gain-negative';
    }

    document.getElementById('top-position').textContent = `${metrics.largest_position} (${metrics.largest_position_percent}%)`;

    // AI Assessment
    // Simple markdown formatting for bold text
    let htmlExplanation = data.explanation.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    htmlExplanation = htmlExplanation.replace(/\n\n/g, '<br><br>');
    document.getElementById('ai-explanation').innerHTML = htmlExplanation;

    // Pros/Cons
    const strengthsUl = document.getElementById('strengths-list');
    strengthsUl.innerHTML = data.positives.map(p => `<li>${p}</li>`).join('');

    const risksUl = document.getElementById('risks-list');
    risksUl.innerHTML = data.risk_highlights.map(r => `<li>${r}</li>`).join('');

    // Tax Table
    if (showTax && data.tax_impacts) {
        document.getElementById('tax-panel').classList.remove('hidden');
        const tbody = document.querySelector('#tax-table tbody');

        tbody.innerHTML = data.tax_impacts.map(t => {
            const taxClass = t.tax_type === 'short_term' ? 'short_term' : 'long_term';
            const typeLabel = t.tax_type === 'short_term' ? 'Short Term' : 'Long Term';
            const gainColor = t.gain_loss >= 0 ? "gain-positive" : "gain-negative";

            return `
                <tr>
                    <td><strong>${t.holding}</strong></td>
                    <td class="${gainColor}">${formatCurrency(t.gain_loss)}</td>
                    <td><span class="badge ${taxClass}">${typeLabel}</span></td>
                    <td>${formatCurrency(t.estimated_tax)} <small style="color:#a1a1aa">(${(t.estimated_tax_rate * 100).toFixed(0)}%)</small></td>
                </tr>
            `;
        }).join('');
    }

    // Rebalancing
    if (showRebalance && data.rebalancing_ideas) {
        document.getElementById('rebalance-panel').classList.remove('hidden');
        const container = document.getElementById('rebalance-list');

        container.innerHTML = data.rebalancing_ideas.map(r => `
            <div class="rebalance-item">
                <div class="reb-action"><i class="fa-solid fa-arrow-right-arrow-left"></i> ${r.action}</div>
                <div class="reb-reason"><strong>Why:</strong> ${r.reason}</div>
                <div class="reb-impact"><strong>Impact:</strong> ${r.impact}</div>
            </div>
        `).join('');
    }

    // Render Chart
    renderChart(metrics.sector_allocation);
}

// Utilities
function formatCurrency(val) {
    // Determine sign string logic
    const isNegative = val < 0;
    const absVal = Math.abs(val);
    const str = '$' + absVal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return isNegative ? '-' + str : str;
}

function renderChart(allocation) {
    const ctx = document.getElementById('sectorChart').getContext('2d');

    // Only show sectors > 0%
    const labels = [];
    const data = [];
    for (const [sec, val] of Object.entries(allocation)) {
        if (val > 0) {
            labels.push(sec);
            data.push(val * 100);
        }
    }

    // Colors mapping to gradient vibe
    const bgColors = ['#8b5cf6', '#ec4899', '#6366f1', '#10b981', '#f59e0b'];

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: bgColors,
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#ffffff' }
                }
            },
            cutout: '70%'
        }
    });
}
