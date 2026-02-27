// State variables
let authToken = localStorage.getItem('auth_token') || null;
let currentUserName = localStorage.getItem('user_name') || null;

// Auth DOM
const authModal = document.getElementById('auth-modal');
const appContainer = document.getElementById('app-container');
const authForm = document.getElementById('auth-form');
const authTitle = document.getElementById('auth-title');
const authSubtitle = document.getElementById('auth-subtitle');
const authSubmitBtn = document.getElementById('auth-submit-btn');
const authSwitchText = document.getElementById('auth-switch-text');
const authSwitchLink = document.getElementById('auth-switch-link');
const nameGroup = document.getElementById('name-group');
const emailGroup = document.getElementById('email-group');
const welcomeName = document.getElementById('welcome-name');
const logoutBtn = document.getElementById('logout-btn');

let isLoginMode = true;

// App DOM
const tbody = document.getElementById('portfolio-body');
const addRowBtn = document.getElementById('add-row-btn');
const analyzeBtn = document.getElementById('analyze-btn');
const sectionUpload = document.getElementById('upload-section');
const sectionLoading = document.getElementById('loading-section');
const sectionResult = document.getElementById('result-section');
const loadingText = document.getElementById('loading-text');
const progressBar = document.getElementById('progress-bar');

// Chat DOM
const chatbotToggle = document.getElementById('chatbot-toggle');
const chatbotWindow = document.getElementById('chatbot-window');
const closeChatBtn = document.getElementById('close-chat');
const sendChatBtn = document.getElementById('send-chat-btn');
const chatInputField = document.getElementById('chat-input-field');
const chatMessagesContainer = document.getElementById('chatbot-messages');

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    checkAuthState();
    addRowBtn.addEventListener('click', addRow);
    analyzeBtn.addEventListener('click', analyzePortfolio);
    setupChatbot();
});

// --- AUTHENTICATION LOGIC ---

authSwitchLink.addEventListener('click', (e) => {
    e.preventDefault();
    isLoginMode = !isLoginMode;
    authForm.reset(); // Clear old values when switching modes
    if (isLoginMode) {
        authTitle.textContent = "Log In to AI Portfolio";
        authSubtitle.textContent = "Analyze, save, and manage your investments.";
        authSubmitBtn.textContent = "Log In";
        authSwitchText.textContent = "Don't have an account?";
        authSwitchLink.textContent = "Register here";
        nameGroup.style.display = "none";
        emailGroup.style.display = "none";
        document.getElementById('register-profile-section').style.display = "none";
        document.getElementById('auth-fullname').required = false;
        document.getElementById('auth-email').required = false;
    } else {
        authTitle.textContent = "Create an Account";
        authSubtitle.textContent = "Join to get personalized AI portfolio analysis.";
        authSubmitBtn.textContent = "Register";
        authSwitchText.textContent = "Already have an account?";
        authSwitchLink.textContent = "Log In here";
        nameGroup.style.display = "block";
        emailGroup.style.display = "block";
        document.getElementById('register-profile-section').style.display = "block";
        document.getElementById('auth-fullname').required = true;
        document.getElementById('auth-email').required = true;
    }
});

authForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.getElementById('auth-username').value;
    const password = document.getElementById('auth-password').value;
    const email = document.getElementById('auth-email').value;
    const fullName = document.getElementById('auth-fullname').value;

    authSubmitBtn.disabled = true;
    authSubmitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';

    try {
        if (isLoginMode) {
            // Login Request
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData
            });

            if (!res.ok) throw new Error("Invalid username or password");
            const data = await res.json();

            authToken = data.access_token;
            currentUserName = data.user_name;
            localStorage.setItem('auth_token', authToken);
            localStorage.setItem('user_name', currentUserName);

        } else {
            // Register Request
            let userProfile = null;
            if (isLoginMode === false && document.getElementById('profile-age').value) {
                userProfile = gatherProfileData(); // Reusing the same function, assuming the inputs have the exact same IDs
            }

            const res = await fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: username,
                    password: password,
                    email: email,
                    full_name: fullName,
                    user_profile: userProfile
                })
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Registration failed");
            }

            // Auto Login immediately after successful registration
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            const loginRes = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData
            });

            if (!loginRes.ok) throw new Error("Auto-login failed. Please try logging in manually.");
            const data = await loginRes.json();

            authToken = data.access_token;
            currentUserName = data.user_name;
            localStorage.setItem('auth_token', authToken);
            localStorage.setItem('user_name', currentUserName);

            // Clear inputs for security
            document.getElementById('auth-password').value = '';

            alert("Registration successful! You are now logged in.");
        }

    } catch (err) {
        alert(err.message);
    } finally {
        authSubmitBtn.disabled = false;
        authSubmitBtn.textContent = isLoginMode ? "Log In" : "Register";
        checkAuthState();
    }
});

logoutBtn.addEventListener('click', () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_name');
    authToken = null;
    currentUserName = null;
    checkAuthState();
});

function checkAuthState() {
    if (authToken) {
        authModal.classList.add('hidden');
        appContainer.classList.remove('hidden');
        welcomeName.innerHTML = `Welcome, <span style="color:var(--primary)">${currentUserName}</span>`;
        loadSavedPortfolio();
        fetchAndSetupProfileUI();
        document.getElementById('floating-edit-profile-btn').style.display = 'block';
    } else {
        authModal.classList.remove('hidden');
        appContainer.classList.add('hidden');
        document.getElementById('floating-edit-profile-btn').style.display = 'none';
    }
}

async function loadSavedPortfolio() {
    try {
        const res = await fetch('/api/portfolio/get', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (res.status === 401) {
            logoutBtn.click();
            return;
        }
        if (res.ok) {
            const holdings = await res.json();
            tbody.innerHTML = ''; // Clear table
            if (holdings.length === 0) {
                addRow();
            } else {
                holdings.forEach(h => addRow(h.ticker, h.shares, h.purchase_price, h.purchase_date));
            }
            analyzeBtn.disabled = false;
        }
    } catch (e) {
        console.error("Failed to load portfolio", e);
    }
}

// --- TABLE LOGIC ---

function addRow(ticker = '', shares = '', price = '', date = '') {
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td><input type="text" class="table-input ticker-input" value="${ticker}" placeholder="e.g. AAPL" required></td>
        <td><input type="number" step="any" min="0.01" class="table-input shares-input" value="${shares}" placeholder="10" required></td>
        <td><input type="number" step="any" min="0.01" class="table-input price-input" value="${price}" placeholder="150.00" required></td>
        <td><input type="date" class="table-input date-input" value="${date}" required></td>
        <td>
            <button class="btn-icon delete-row-btn" title="Remove row">
                <i class="fa-solid fa-trash"></i>
            </button>
        </td>
    `;
    tbody.appendChild(tr);

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
            current_price: null
        });
    }
    return holdings;
}

// --- PROFILE MODAL & LOGIC ---

// This function still works because the form fields have the exact same IDs in the Auth Modal
function gatherProfileData(prefix = "profile") {
    const ageVal = document.getElementById(`${prefix}-age`).value;
    return {
        age: ageVal ? parseInt(ageVal, 10) : null,
        profession: document.getElementById(`${prefix}-profession`).value,
        annual_income: document.getElementById(`${prefix}-income`).value,
        investment_experience: document.getElementById(`${prefix}-experience`).value,
        risk_appetite: document.getElementById(`${prefix}-risk`).value,
        investment_horizon: document.getElementById(`${prefix}-horizon`).value,
        dependents: document.getElementById(`${prefix}-dependents`).value,
        primary_goal: document.getElementById(`${prefix}-goal`).value
    };
}

let userProfileBackup = null;

async function fetchAndSetupProfileUI() {
    try {
        const res = await fetch('/api/profile', { headers: { 'Authorization': `Bearer ${authToken}` } });
        if (res.ok) {
            userProfileBackup = await res.json();
        }
    } catch (e) { console.error("Could not fetch profile", e); }
}

const editProfileBtn = document.getElementById('floating-edit-profile-btn');
const editProfileModal = document.getElementById('edit-profile-modal');
const closeEditProfileBtn = document.getElementById('close-edit-profile-btn');
const saveEditProfileBtn = document.getElementById('save-edit-profile-btn');
const editProfileGrid = document.getElementById('edit-profile-grid');

// Clone the registration fields into the modal safely
function openEditProfileModal() {
    try {

        // Pre-fill fields safely
        if (userProfileBackup) {
            const selAge = document.getElementById('edit-profile-age');
            if (selAge && userProfileBackup.age) selAge.value = userProfileBackup.age;

            const selProf = document.getElementById('edit-profile-profession');
            if (selProf && userProfileBackup.profession) selProf.value = userProfileBackup.profession;

            const selInc = document.getElementById('edit-profile-income');
            if (selInc && userProfileBackup.annual_income) selInc.value = userProfileBackup.annual_income;

            const selExp = document.getElementById('edit-profile-experience');
            if (selExp && userProfileBackup.investment_experience) selExp.value = userProfileBackup.investment_experience;

            const selRisk = document.getElementById('edit-profile-risk');
            if (selRisk && userProfileBackup.risk_appetite) selRisk.value = userProfileBackup.risk_appetite;

            const selHor = document.getElementById('edit-profile-horizon');
            if (selHor && userProfileBackup.investment_horizon) selHor.value = userProfileBackup.investment_horizon;

            const selDep = document.getElementById('edit-profile-dependents');
            if (selDep && userProfileBackup.dependents) selDep.value = userProfileBackup.dependents;

            const selGoal = document.getElementById('edit-profile-goal');
            if (selGoal && userProfileBackup.primary_goal) selGoal.value = userProfileBackup.primary_goal;
        }

        editProfileModal.style.display = 'block';
    } catch (err) {
        console.error("Error opening profile modal: ", err);
        alert("There was an issue opening the edit modal. Please reload.");
    }
}

editProfileBtn.addEventListener('click', openEditProfileModal);

closeEditProfileBtn.addEventListener('click', () => {
    editProfileModal.style.display = 'none';
});

saveEditProfileBtn.addEventListener('click', async () => {
    try {
        const newProfile = gatherProfileData('edit-profile');
        saveEditProfileBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';

        const res = await fetch('/api/profile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(newProfile)
        });

        if (res.ok) {
            userProfileBackup = await res.json();
            editProfileModal.style.display = 'none';
            // Auto re-analyze to instantly see standard updates matching the new DB profile!
            if (!sectionResult.classList.contains('hidden') || !sectionUpload.classList.contains('hidden')) {
                // Only re-trigger if they've at least added stocks
                if (tbody.querySelectorAll('tr').length > 0) {
                    analyzePortfolio();
                }
            }
        } else {
            console.error(await res.text());
            alert("Failed to save profile. See console.");
        }
    } catch (e) {
        console.error("Save profile error:", e);
        alert("Error saving profile! " + e.message);
    } finally {
        saveEditProfileBtn.innerHTML = 'Save &amp; Re-preview';
    }
});

// --- APP FLOW (Explain) ---

async function analyzePortfolio() {
    sectionUpload.classList.add('hidden');
    sectionLoading.classList.remove('hidden');

    try {
        let parsedHoldings = [];
        try {
            parsedHoldings = gatherPortfolioData();
        } catch (e) {
            sectionLoading.classList.add('hidden');
            sectionUpload.classList.remove('hidden');
            alert(e.message);
            return;
        }

        updateLoadingState(`Saving portfolio securely...`, 20);

        // Save to DB First
        await fetch('/api/portfolio/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(parsedHoldings)
        });

        updateLoadingState(`Fetching real-time prices and creating personalized JSON insight...`, 50);

        const userLevel = document.getElementById('user-level').value;

        // Explain payload drops `user_profile` now since the backend natively loads it from the DB
        const explainReqPayload = {
            portfolio: parsedHoldings,
            user_level: userLevel,
            include_tax_analysis: true,
            include_rebalancing: true,
            transcript_context: null
        };

        const explainRes = await fetch('/api/explain', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(explainReqPayload)
        });

        if (!explainRes.ok) {
            if (explainRes.status === 401) {
                logoutBtn.click();
                throw new Error("Session expired. Please log in again.");
            }
            const errData = await explainRes.json();
            throw new Error(errData.detail || 'Failed to generate JSON logic');
        }

        const reportData = await explainRes.json();
        updateLoadingState("Rendering dashboard...", 100);

        setTimeout(() => {
            renderDashboard(reportData);
        }, 500);

    } catch (error) {
        alert("Error: " + error.message);
        sectionLoading.classList.add('hidden');
        sectionUpload.classList.remove('hidden');
    }
}

function updateLoadingState(text, percent) {
    loadingText.textContent = text;
    progressBar.style.width = `${percent}%`;
}

// --- RENDER DASHBOARD (NEW JSON SCHEMA) ---

function renderDashboard(data) {
    sectionLoading.classList.add('hidden');
    sectionResult.classList.remove('hidden');

    const metrics = data.portfolio_metrics;

    // Top Stats
    document.getElementById('total-value').textContent = formatCurrency(metrics.total_value);
    const gainEl = document.getElementById('total-gain');
    gainEl.textContent = `${formatCurrency(metrics.unrealized_gain)} (${metrics.unrealized_gain_percent > 0 ? '+' : ''}${metrics.unrealized_gain_percent}%)`;
    gainEl.className = metrics.unrealized_gain >= 0 ? 'gain-positive' : 'gain-negative';
    document.getElementById('top-position').textContent = `${metrics.largest_position} (${metrics.largest_position_percent}%)`;

    // Suitability metrics
    const score = metrics.suitability_score || 0;
    let color = 'var(--text)';
    if (score >= 75) color = 'var(--success)';
    else if (score >= 50) color = 'var(--warning)';
    else color = 'var(--danger)';

    const suitScoreEl = document.getElementById('suitability-score');
    suitScoreEl.textContent = `${score}/100`;
    suitScoreEl.style.color = color;

    const suitLevelEl = document.getElementById('suitability-level');
    suitLevelEl.textContent = metrics.suitability_level || "Unknown";
    suitLevelEl.style.color = color;

    document.getElementById('life-stage').textContent = metrics.life_stage_classification || "Unknown";

    const breakdownUl = document.getElementById('suitability-breakdown');
    if (metrics.suitability_breakdown && metrics.suitability_breakdown.length > 0) {
        breakdownUl.innerHTML = metrics.suitability_breakdown.map(b => `<li>${b}</li>`).join('');
    } else {
        breakdownUl.innerHTML = '<li>No warnings. Aligned with profile.</li>';
    }

    // 1. AI Greeting & Summary
    let htmlExplanation = `
        <h3 style="color:var(--primary); margin-bottom: 0.5rem">${data.greeting}</h3>
        <p>${data.portfolio_summary}</p>
        <p style="margin-top:1rem; color:var(--text-secondary)"><strong>Confidence Score:</strong> ${(data.confidence_score * 100).toFixed(0)}%</p>
    `;
    document.getElementById('ai-explanation').innerHTML = htmlExplanation;

    // 2. Key Takeaways replacing Strengths
    const strengthsUl = document.getElementById('strengths-list');
    document.querySelector('.strengths h3').innerHTML = '<i class="fa-solid fa-lightbulb"></i> Key Takeaways';
    strengthsUl.innerHTML = data.key_takeaways.map(p => `<li>${p}</li>`).join('');

    // 3. Action Plan replacing Risks
    const risksUl = document.getElementById('risks-list');
    document.querySelector('.risks h3').innerHTML = '<i class="fa-solid fa-list-check"></i> Action Plan';
    risksUl.innerHTML = data.action_plan.map(r => `<li>${r}</li>`).join('');

    // 4. Per Stock Analysis rendering explicitly replacing Rebalancing Idea panel logic visually
    document.getElementById('rebalance-panel').classList.remove('hidden');
    document.querySelector('.rebalance-panel h3').innerHTML = '<i class="fa-solid fa-magnifying-glass-chart"></i> Per-Asset Transcript Insights';
    const container = document.getElementById('rebalance-list');

    container.innerHTML = data.per_stock_analysis.map(s => `
        <div class="rebalance-item">
            <div class="reb-action" style="font-size: 1.1rem; color: var(--primary)"><i class="fa-solid fa-briefcase"></i> ${s.ticker}</div>
            <div class="reb-reason"><strong>Performance:</strong> ${s.performance_summary}</div>
            <div class="reb-reason"><strong>Signals:</strong> ${s.risk_signals_from_transcripts.join(' ')}</div>
            <div class="reb-impact"><strong>Tax Advice:</strong> ${s.tax_consideration}</div>
        </div>
    `).join('');

    // 5. General Tax Advice Panel replacing the old Tax Table
    document.getElementById('tax-panel').classList.remove('hidden');
    document.querySelector('#tax-panel h3').innerHTML = '<i class="fa-solid fa-scale-unbalanced"></i> Risk & Tax Optimization';

    document.querySelector('#tax-panel .table-container').innerHTML = `
        <div style="background: rgba(0,0,0,0.2); border: 1px solid var(--panel-border); border-radius:10px; padding: 1.5rem">
            <p style="margin-bottom: 1rem"><strong>Risk Explanation:</strong><br/> ${data.risk_score_explanation}</p>
            <p style="color:var(--success)"><strong>Tax Optimization Advice:</strong><br/> ${data.tax_optimization_advice}</p>
        </div>
    `;

    // Render Chart
    renderChart(metrics.sector_allocation);
}

// Utilities
function formatCurrency(val) {
    const isNegative = val < 0;
    const absVal = Math.abs(val);
    const str = '$' + absVal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return isNegative ? '-' + str : str;
}

function renderChart(allocation) {
    // Destroy previous instance to prevent breaking on re-render
    const existingChart = Chart.getChart("sectorChart");
    if (existingChart) existingChart.destroy();

    const ctx = document.getElementById('sectorChart').getContext('2d');

    const labels = [];
    const data = [];
    for (const [sec, val] of Object.entries(allocation)) {
        if (val > 0) {
            labels.push(sec);
            data.push(val * 100);
        }
    }

    const bgColors = ['#10b981', '#d97706', '#059669', '#f59e0b', '#34d399'];

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
                    labels: { color: '#111827' }
                }
            },
            cutout: '70%'
        }
    });
}

// --- CHATBOT LOGIC ---

function setupChatbot() {
    // Open chat
    chatbotToggle.addEventListener('click', () => {
        chatbotWindow.classList.add('open');
        chatInputField.focus();
    });

    // Close chat
    closeChatBtn.addEventListener('click', () => {
        chatbotWindow.classList.remove('open');
    });

    // Send message on click
    sendChatBtn.addEventListener('click', handleSendChatMessage);

    // Send message on enter
    chatInputField.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSendChatMessage();
    });
}

async function handleSendChatMessage() {
    const text = chatInputField.value.trim();
    if (!text) return;

    // 1. Add User Message
    addChatMessage(text, 'user');
    chatInputField.value = '';

    // 2. Add Loading Indicator
    const loaderId = addChatLoader();

    try {
        // 3. Send API Request
        // If the user isn't logged in with a token, we could omit the Authorization header,
        // but for now we expect they are authenticated for the chatbot as well.
        const reqHeaders = { 'Content-Type': 'application/json' };
        if (authToken) {
            reqHeaders['Authorization'] = `Bearer ${authToken}`;
        }

        const res = await fetch('/chat/message', {
            method: 'POST',
            headers: reqHeaders,
            body: JSON.stringify({ message: text, top_k_sources: 5 })
        });

        removeChatLoader(loaderId);

        if (!res.ok) {
            throw new Error(`Server returned ${res.status}`);
        }

        const data = await res.json();

        // 4. Render Bot Response
        addChatMessage(data.reply, 'bot', data.detected_stocks);

    } catch (err) {
        console.error(err);
        removeChatLoader(loaderId);
        addChatMessage("Sorry, I encountered an error connecting to the server.", 'bot');
    }
}

function addChatMessage(message, sender, detectedStocks = null) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${sender}`;

    let contentHtml = `<p>${escapeHtml(message)}</p>`;

    if (detectedStocks && detectedStocks.length > 0) {
        contentHtml += `<span class="chat-metadata">Detected: ${detectedStocks.join(', ')}</span>`;
    }

    msgDiv.innerHTML = contentHtml;
    chatMessagesContainer.appendChild(msgDiv);

    // Scroll to bottom
    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
}

function addChatLoader() {
    const id = 'loader-' + Date.now();
    const loaderDiv = document.createElement('div');
    loaderDiv.className = 'chat-loader';
    loaderDiv.id = id;
    loaderDiv.innerHTML = `
        <div class="chat-dot"></div>
        <div class="chat-dot"></div>
        <div class="chat-dot"></div>
    `;
    chatMessagesContainer.appendChild(loaderDiv);
    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
    return id;
}

function removeChatLoader(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/'/g, "&#039;");
}

// --- INITIALIZATION ---
analyzeBtn.addEventListener('click', analyzePortfolio);
addRowBtn.addEventListener('click', () => addRow());
setupChatbot();
checkAuthState();
