// Dynamically detect the backend URL
// REPLACE 'https://your-backend-url.onrender.com' with your actual Render URL after deployment
const PRODUCTION_BACKEND_URL = "https://careermind-ai-backend.onrender.com";
const API_BASE_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? "http://localhost:8000"
    : PRODUCTION_BACKEND_URL;

// Global state
let studentKey = localStorage.getItem("student_key") || "";
let studentPassword = localStorage.getItem("student_password") || "";
let studentFirstName = localStorage.getItem("student_first_name") || "Student";
let studentKeyOnboarding = "";
let studentPasswordOnboarding = "";

// Helper for downloading images (handles cross-origin issues)
async function downloadImage(url, filename) {
    try {
        const response = await fetch(url);
        const blob = await response.blob();
        const blobUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = blobUrl;
        link.download = filename || 'careermind_image.png';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(blobUrl);
    } catch (error) {
        console.error("Download failed:", error);
        window.open(url, '_blank');
    }
}

const onboardingQuestions = [
    "Which degree/class are you studying?",
    "Which semester/year are you in?",
    "What is your specialization?",
    "What do you want to become?",
    "Which programming languages or skills do you know?",
    "Which topics are weak for you?",
    "How many hours can you study daily?"
];

// ---------- Chat History Management ----------
let chatHistories = [];
let currentChatId = null;
let currentChatMessages = [];

function loadChatHistories() {
    if (!studentKey) {
        chatHistories = [];
        return;
    }
    try {
        const saved = localStorage.getItem(`careermind_chat_histories_${studentKey}`);
        if (saved) {
            chatHistories = JSON.parse(saved);
        } else {
            chatHistories = [];
        }
    } catch (e) {
        chatHistories = [];
    }
}

function saveChatHistories() {
    if (!studentKey) return;
    localStorage.setItem(`careermind_chat_histories_${studentKey}`, JSON.stringify(chatHistories));
}

function renderHistoryList() {
    const list = document.getElementById("history-list");
    if (!list) return;

    list.innerHTML = chatHistories.map(chat => {
        const activeClass = chat.id === currentChatId ? "active" : "";
        return `
            <div class="history-item ${activeClass}" data-chat-id="${chat.id}" onclick="openChatHistory('${chat.id}')">
                <i class="fa-regular fa-message"></i>
                <span>${escapeHTML(chat.title || "Untitled chat")}</span>
            </div>
        `;
    }).join("");
}

function startNewChat() {
    if (currentChatMessages.length > 0 && !currentChatId) {
        const firstUserMsg = currentChatMessages.find(m => m.type === 'user');
        const title = firstUserMsg ? firstUserMsg.content.substring(0, 50) : "New chat";
        const newHistory = {
            id: Date.now().toString(),
            title: title,
            messages: JSON.parse(JSON.stringify(currentChatMessages))
        };
        chatHistories.push(newHistory);
        saveChatHistories();
    }

    currentChatId = null;
    currentChatMessages = [];

    const outputArea = document.getElementById("output-area");
    const welcomeScreen = document.getElementById("welcome-screen");
    const input = document.getElementById("user-question");

    if (outputArea) outputArea.innerHTML = "";
    if (welcomeScreen) welcomeScreen.classList.remove("hidden");
    if (input) {
        input.value = "";
        input.style.height = "auto";
    }

    renderHistoryList();
    closeSidebarOnMobile();
    scrollToBottom();
}

function openChatHistory(chatId) {
    const chat = chatHistories.find(c => c.id === chatId);
    if (!chat) return;

    if (currentChatMessages.length > 0 && !currentChatId) {
        const firstUserMsg = currentChatMessages.find(m => m.type === 'user');
        const title = firstUserMsg ? firstUserMsg.content.substring(0, 50) : "New chat";
        const newHistory = {
            id: Date.now().toString(),
            title: title,
            messages: JSON.parse(JSON.stringify(currentChatMessages))
        };
        chatHistories.push(newHistory);
    }

    currentChatId = chatId;
    currentChatMessages = JSON.parse(JSON.stringify(chat.messages));

    const outputArea = document.getElementById("output-area");
    const welcomeScreen = document.getElementById("welcome-screen");

    welcomeScreen.classList.add("hidden");
    outputArea.innerHTML = "";

    currentChatMessages.forEach(msg => {
        if (msg.type === 'user') {
            const msgDiv = document.createElement("div");
            msgDiv.className = "message-row user";
            msgDiv.innerHTML = `<div class="message-bubble">${escapeHTML(msg.content)}</div>`;
            outputArea.appendChild(msgDiv);
        } else {
            const msgDiv = document.createElement("div");
            msgDiv.className = "message-row ai";
            const safeAnswer = escapeHTML(msg.content);
            const sourcesHtml = renderSources(msg.sources || []);

            // Render basic message structure
            msgDiv.innerHTML = `
                <div class="message-bubble">
                    <div class="message-sender">CareerMind AI</div>
                    <div class="message-content">${safeAnswer}</div>
                    ${sourcesHtml}
                </div>
            `;

            // If message has an image URL, add it
            if (msg.imageUrl) {
                const fullImageUrl = msg.imageUrl.startsWith("http") ? msg.imageUrl : `${API_BASE_URL}${msg.imageUrl}`;
                const imageHtml = `
                    <div class="generated-image-card">
                        <div class="generated-image-wrapper">
                            <img src="${fullImageUrl}" alt="Generated image" class="generated-image" loading="lazy">
                        </div>
                        <div class="image-actions">
                            <button onclick="downloadImage('${fullImageUrl}', 'careermind_image_${Date.now()}.png')" class="download-btn">
                                <i class="fa-solid fa-download"></i> Download Image
                            </button>
                        </div>
                    </div>
                `;
                msgDiv.querySelector(".message-bubble").insertAdjacentHTML('beforeend', imageHtml);
            }
            outputArea.appendChild(msgDiv);
        }
    });

    renderHistoryList();
    scrollToBottom();
}

// ---------- Auth & UI helpers ----------
// ---------- Auth & UI helpers ----------
window.onload = function () {
    // Splash screen timer
    const splash = document.getElementById("splash-screen");
    if (splash) {
        setTimeout(() => {
            splash.style.opacity = "0";
            setTimeout(() => {
                splash.style.display = "none";
                initAppFlow();
            }, 800);
        }, 2000);
    } else {
        initAppFlow();
    }
};

function initAppFlow() {
    safeClearRegistrationForm();
    initChatHandlers();
    loadChatHistories();
    renderHistoryList();
    initSidebarResize();

    // Force start on Register page as requested
    showRegister();
}

function initChatHandlers() {
    const textarea = document.getElementById("user-question");
    if (!textarea) return;

    textarea.addEventListener("input", function () {
        this.style.height = "auto";
        this.style.height = `${Math.min(this.scrollHeight, 180)}px`;
    });

    textarea.addEventListener("keydown", function (event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            askSmartAgent();
        }
    });
}

function showRegister() {
    hideAllSections();
    document.getElementById("register-section").classList.remove("hidden");
    safeClearRegistrationForm();
    const registerResult = document.getElementById("register-result");
    if (registerResult) registerResult.innerHTML = "";
}

function showLogin() {
    hideAllSections();
    document.getElementById("login-section").classList.remove("hidden");

    // Clear login boxes to prevent accidental auto-fill
    const p1 = document.getElementById("key-part1");
    const p2 = document.getElementById("key-part2");
    const p3 = document.getElementById("key-part3");
    const pass = document.getElementById("login-password");

    if (p1) p1.value = "";
    if (p2) p2.value = "";
    if (p3) p3.value = "";
    if (pass) pass.value = "";

    const loginResult = document.getElementById("login-result");
    if (loginResult) loginResult.innerHTML = "";

    if (p1) p1.focus();
}

function showDashboard() {
    hideAllSections();
    document.getElementById("dashboard-section").classList.remove("hidden");
    updateWelcomeMessage();
    renderHistoryList();

    const input = document.getElementById("user-question");
    if (input) input.focus();
}

function showOnboarding(newStudentKey, newStudentPassword) {
    studentKeyOnboarding = newStudentKey;
    studentPasswordOnboarding = newStudentPassword;

    hideAllSections();
    document.getElementById("onboarding-section").classList.remove("hidden");
    renderOnboardingQuestions();
}

function hideAllSections() {
    const sections = [
        "register-section",
        "login-section",
        "onboarding-section",
        "dashboard-section"
    ];
    sections.forEach(id => {
        const section = document.getElementById(id);
        if (section) section.classList.add("hidden");
    });
}

function updateWelcomeMessage() {
    const welcomeMessage = document.getElementById("welcome-message");
    if (!welcomeMessage) return;
    if (studentFirstName) {
        welcomeMessage.textContent = `Welcome Back, ${studentFirstName}!`;
    } else {
        welcomeMessage.textContent = "Welcome Back!";
    }
}

function safeClearRegistrationForm() {
    const fields = [
        "reg-first-name",
        "reg-middle-name",
        "reg-last-name",
        "reg-email",
        "reg-password",
        "reg-confirm-password"
    ];
    fields.forEach(id => {
        const field = document.getElementById(id);
        if (field) field.value = "";
    });
}

function renderOnboardingQuestions() {
    const container = document.getElementById("onboarding-questions-container");
    if (!container) return;
    container.innerHTML = "";
    onboardingQuestions.forEach((question, index) => {
        const questionDiv = document.createElement("div");
        questionDiv.className = "form-group";
        questionDiv.innerHTML = `
            <label for="onboarding-q${index}">
                ${index + 1}. ${escapeHTML(question)}
            </label>
            <textarea 
                id="onboarding-q${index}" 
                placeholder="Your answer here..." 
                rows="2"
                required
            ></textarea>
        `;
        container.appendChild(questionDiv);
    });
}

async function submitOnboarding() {
    const resultBox = document.getElementById("onboarding-result");
    const submitButton = document.getElementById("onboarding-submit");
    const answers = [];
    let valid = true;

    for (let i = 0; i < onboardingQuestions.length; i++) {
        const answerBox = document.getElementById(`onboarding-q${i}`);
        const answer = answerBox ? answerBox.value.trim() : "";
        if (!answer) {
            valid = false;
            break;
        }
        answers.push({
            question: onboardingQuestions[i],
            answer: answer
        });
    }

    if (!valid) {
        showError(resultBox, "Please answer all questions.");
        return;
    }

    setButtonLoading(submitButton, true, "Saving...");
    resultBox.innerHTML = "";

    try {
        const response = await fetch(`${API_BASE_URL}/onboarding`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                student_key: studentKeyOnboarding,
                password: studentPasswordOnboarding,
                answers: answers
            })
        });
        const data = await response.json();
        if (data.success) {
            studentKey = studentKeyOnboarding;
            studentPassword = studentPasswordOnboarding;
            localStorage.setItem("student_key", studentKey);
            localStorage.setItem("student_password", studentPassword);
            showSuccess(resultBox, "Profile setup complete. Redirecting to dashboard...");
            setTimeout(() => showDashboard(), 1200);
        } else {
            showError(resultBox, data.message || "Failed to save onboarding answers.");
        }
    } catch (error) {
        showError(resultBox, `Connection error: ${error.message}`);
    } finally {
        setButtonLoading(submitButton, false, "Complete Setup");
    }
}

async function registerStudent() {
    const firstName = document.getElementById("reg-first-name").value.trim();
    const middleName = document.getElementById("reg-middle-name").value.trim();
    const lastName = document.getElementById("reg-last-name").value.trim();
    const email = document.getElementById("reg-email").value.trim();
    const password = document.getElementById("reg-password").value;
    const confirmPassword = document.getElementById("reg-confirm-password").value;
    const resultBox = document.getElementById("register-result");
    const button = document.querySelector("#register-section form button[type='submit']");

    if (!firstName || !lastName || !email || !password || !confirmPassword) {
        showError(resultBox, "Please fill in all required fields.");
        return;
    }
    if (password !== confirmPassword) {
        showError(resultBox, "Passwords do not match.");
        return;
    }
    if (!isValidEmail(email)) {
        showError(resultBox, "Please enter a valid email address.");
        return;
    }
    if (password.length < 6) {
        showError(resultBox, "Password must be at least 6 characters.");
        return;
    }

    setButtonLoading(button, true, "Registering...");
    resultBox.innerHTML = "";

    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                first_name: firstName,
                middle_name: middleName,
                last_name: lastName,
                email: email,
                password: password
            })
        });
        const data = await response.json();
        if (data.registration && data.registration.success) {
            clearSession(); // Wipe any old data before starting new account
            studentFirstName = firstName;
            localStorage.setItem("student_first_name", studentFirstName);
            showSuccess(resultBox, "Account created. Your student key has been sent to your email. Now complete your profile.");
            safeClearRegistrationForm();
            setTimeout(() => showOnboarding(data.registration.student_key, password), 1300);
        } else {
            showError(resultBox, data.registration?.message || "Registration failed. Please try again.");
        }
    } catch (error) {
        showError(resultBox, `Connection error: ${error.message}`);
    } finally {
        setButtonLoading(button, false, "Create Account");
    }
}

function handleKeyInput(current, nextId) {
    if (current.value.length >= current.maxLength) {
        const next = document.getElementById(nextId);
        if (next) next.focus();
    }
}

async function loginStudent() {
    const p1 = document.getElementById("key-part1").value.trim();
    const p2 = document.getElementById("key-part2").value.trim();
    const p3 = document.getElementById("key-part3").value.trim();
    const password = document.getElementById("login-password").value;
    const resultBox = document.getElementById("login-result");
    const button = document.querySelector("#login-section form button[type='submit']");

    const key = `${p1}${p2}-${p3}`.toUpperCase();

    if (!p1 || !p2 || !p3 || !password) {
        showError(resultBox, "Please enter your complete Student Key and Password.");
        return;
    }

    setButtonLoading(button, true, "Signing In...");
    resultBox.innerHTML = "";

    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ student_key: key, password: password })
        });
        const data = await response.json();
        if (data.success) {
            clearSession(); // Wipe any old data before logging in
            studentKey = key;
            studentPassword = password;
            if (data.student && data.student.first_name) {
                studentFirstName = data.student.first_name;
            }
            localStorage.setItem("student_key", studentKey);
            localStorage.setItem("student_password", studentPassword);
            localStorage.setItem("student_first_name", studentFirstName);

            // Reload user-specific history
            loadChatHistories();

            // Enforce onboarding check
            if (data.onboarding_completed === false) {
                showSuccess(resultBox, "Login successful. Please complete your profile first.");
                setTimeout(() => showOnboarding(studentKey, studentPassword), 1200);
            } else {
                showSuccess(resultBox, "Login successful. Redirecting...");
                setTimeout(() => showDashboard(), 1000);
            }
        } else {
            showError(resultBox, data.message || "Login failed. Please check your credentials.");
        }
    } catch (error) {
        showError(resultBox, `Connection error: ${error.message}`);
    } finally {
        setButtonLoading(button, false, "Sign In");
    }
}

function logout() {
    clearSession();
    showLogin();
}

function clearSession() {
    localStorage.removeItem("student_key");
    localStorage.removeItem("student_password");
    localStorage.removeItem("student_first_name");

    // Full session reset
    studentKey = "";
    studentPassword = "";
    studentFirstName = "";
    chatHistories = [];
    currentChatId = null;
    currentChatMessages = [];

    const outputArea = document.getElementById("output-area");
    const input = document.getElementById("user-question");
    const welcomeScreen = document.getElementById("welcome-screen");
    const historyList = document.getElementById("chat-history-list");

    if (outputArea) outputArea.innerHTML = "";
    if (input) input.value = "";
    if (welcomeScreen) welcomeScreen.classList.remove("hidden");
    if (historyList) historyList.innerHTML = "";
}

// ---------- UI utilities ----------
function showError(element, message) {
    if (!element) return;
    element.innerHTML = `<div class="error-message">✗ ${escapeHTML(message)}</div>`;
    shakeInputBox();
}

function showSuccess(element, message) {
    if (!element) return;
    element.innerHTML = `<div class="success-message">✓ ${escapeHTML(message)}</div>`;
}

function setButtonLoading(button, isLoading, text) {
    if (!button) return;
    button.disabled = isLoading;
    button.textContent = text;
}

function isValidEmail(email) {
    // Professional-grade email validation regex
    return /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(email);
}

function escapeHTML(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function escapeAttribute(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll('"', "&quot;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
}

function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    const expandBtn = document.getElementById("expand-sidebar-btn");
    if (!sidebar) return;

    sidebar.classList.toggle("collapsed");

    if (expandBtn) {
        if (sidebar.classList.contains("collapsed")) {
            expandBtn.classList.remove("hidden");
        } else {
            expandBtn.classList.add("hidden");
        }
    }
}

function closeSidebarOnMobile() {
    if (window.innerWidth > 768) return;
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebar-overlay");
    if (sidebar) sidebar.classList.remove("open");
    if (overlay) overlay.classList.remove("show");
}

function togglePasswordVisibility(inputId, icon) {
    const input = document.getElementById(inputId);
    if (!input || !icon) return;

    if (input.type === "password") {
        input.type = "text";
        icon.classList.remove("fa-eye");
        icon.classList.add("fa-eye-slash");
    } else {
        input.type = "password";
        icon.classList.remove("fa-eye-slash");
        icon.classList.add("fa-eye");
    }
}

function useSuggestion(text) {
    const input = document.getElementById("user-question");
    if (!input) return;
    input.value = text;
    input.focus();
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 180)}px`;
}

function toggleSources(contentId, iconId) {
    const content = document.getElementById(contentId);
    const icon = document.getElementById(iconId);
    if (!content || !icon) return;
    content.classList.toggle("open");
    if (content.classList.contains("open")) {
        icon.className = "fa-solid fa-chevron-up";
    } else {
        icon.className = "fa-solid fa-chevron-down";
    }
}

function scrollToBottom(smooth = false) {
    const chatWindow = document.getElementById("chat-window");
    if (!chatWindow) return;
    if (smooth) {
        chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: "smooth" });
    } else {
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
}

// ---------- Source handling ----------
function cleanAnswerText(answer) {
    if (!answer) return "CareerMind AI could not generate an answer right now.";
    const text = String(answer).trim();
    const lowered = text.toLowerCase();

    // Only hide if it's a short error message (not a normal long answer)
    if (text.length <= 200) {
        const errorKeywords = [
            "llm error",
            "resource_exhausted",
            "generate_content_free_tier",
            "quota exceeded",
            "rate limit",
            "429",
            "traceback",
            "bad request",
            "403 forbidden"
        ];
        for (const keyword of errorKeywords) {
            if (lowered.includes(keyword)) {
                return "CareerMind AI is temporarily busy. Please try again after a few seconds.";
            }
        }
    }
    return text;
}

function extractSources(data) {
    if (!data) return [];
    if (Array.isArray(data.sources) && data.sources.length > 0) return data.sources;
    if (Array.isArray(data.web_sources) && data.web_sources.length > 0) return data.web_sources;
    if (Array.isArray(data.rag_sources) && data.rag_sources.length > 0) return data.rag_sources;
    return [];
}

function renderSources(sources) {
    if (!sources || sources.length === 0) return "";
    const contentId = `sources-${Date.now()}-${Math.floor(Math.random() * 10000)}`;
    const iconId = `icon-${contentId}`;
    const sourceItems = sources.map((source, index) => {
        const title = escapeHTML(source.title || source.source || `Source ${index + 1}`);
        const score = source.score ? ` <span style="color:#858585;">Score: ${Number(source.score).toFixed(4)}</span>` : "";
        if (source.url) {
            const safeUrl = escapeAttribute(source.url);
            return `<div class="source-item">${index + 1}. <a href="${safeUrl}" target="_blank" rel="noopener noreferrer">${title}</a>${score}</div>`;
        }
        return `<div class="source-item">${index + 1}. ${title}${score}</div>`;
    }).join("");

    return `
        <div class="sources-container">
            <div class="sources-header" onclick="toggleSources('${contentId}', '${iconId}')">
                <span><i class="fa-solid fa-layer-group"></i> Sources (${sources.length})</span>
                <i id="${iconId}" class="fa-solid fa-chevron-down"></i>
            </div>
            <div class="sources-content" id="${contentId}">${sourceItems}</div>
        </div>
    `;
}

function appendUserMessage(message) {
    const outputArea = document.getElementById("output-area");
    if (!outputArea) return;
    const msg = document.createElement("div");
    msg.className = "message-row user fade-in";
    msg.innerHTML = `<div class="message-bubble">${escapeHTML(message)}</div>`;
    outputArea.appendChild(msg);
    setTimeout(() => msg.classList.remove("fade-in"), 400);
    scrollToBottom(true);
}

function appendLoadingMessage() {
    const outputArea = document.getElementById("output-area");
    const loadingId = `loading-${Date.now()}`;
    const msg = document.createElement("div");
    msg.className = "message-row ai fade-in";
    msg.id = loadingId;
    msg.innerHTML = `
        <div class="message-bubble">
            <div class="message-sender">CareerMind AI</div>
            <div class="message-content">
                <span class="typing-dots">
                    <span class="dot"></span><span class="dot"></span><span class="dot"></span>
                </span>
            </div>
        </div>
    `;
    outputArea.appendChild(msg);
    setTimeout(() => msg.classList.remove("fade-in"), 400);
    scrollToBottom(true);
    return loadingId;
}

function removeMessageById(id) {
    const element = document.getElementById(id);
    if (element) {
        element.classList.add("fade-out");
        setTimeout(() => element.remove(), 350);
    }
}

function appendAIMessage(answer, sources = []) {
    const outputArea = document.getElementById("output-area");
    const msg = document.createElement("div");
    msg.className = "message-row ai fade-in";
    const safeAnswer = escapeHTML(cleanAnswerText(answer));
    const sourcesHtml = renderSources(sources);
    msg.innerHTML = `
        <div class="message-bubble">
            <div class="message-sender">CareerMind AI</div>
            <div class="message-content">${safeAnswer}</div>
            ${sourcesHtml}
        </div>
    `;
    outputArea.appendChild(msg);
    setTimeout(() => msg.classList.remove("fade-in"), 400);
    scrollToBottom(true);
}

// Add an AI message with an optional image
function appendAIImageMessage(text, imageUrl, sources = []) {
    const outputArea = document.getElementById("output-area");
    const msg = document.createElement("div");
    msg.className = "message-row ai fade-in";

    // Ensure the image URL points to the correct backend port
    const fullImageUrl = imageUrl.startsWith("http") ? imageUrl : `${API_BASE_URL}${imageUrl}`;

    // Use the clean success message
    const cleanText = text.toLowerCase().includes("generated an image")
        ? "Image generated successfully! Now you can download it."
        : escapeHTML(cleanAnswerText(text));

    const sourcesHtml = renderSources(sources);

    msg.innerHTML = `
        <div class="message-bubble">
            <div class="message-sender">CareerMind AI</div>
            <div class="message-content">${cleanText}</div>
            <div class="generated-image-card">
                <div class="generated-image-wrapper">
                    <img src="${fullImageUrl}" alt="Generated image" class="generated-image" loading="lazy">
                </div>
                <div class="image-actions">
                    <button onclick="downloadImage('${fullImageUrl}', 'careermind_image_${Date.now()}.png')" class="download-btn">
                        <i class="fa-solid fa-download"></i> Download Image
                    </button>
                </div>
            </div>
            ${sourcesHtml}
        </div>
    `;
    outputArea.appendChild(msg);
    setTimeout(() => msg.classList.remove("fade-in"), 400);
    scrollToBottom(true);
}


function shakeInputBox() {
    const input = document.getElementById("user-question");
    if (!input) return;
    input.classList.add("shake");
    setTimeout(() => input.classList.remove("shake"), 500);
}

// ---------- Sidebar Resize ----------
let isResizing = false;
let startX, startWidth;

function initSidebarResize() {
    const handle = document.getElementById("sidebar-resize-handle");
    if (!handle) return;

    handle.addEventListener("mousedown", function (e) {
        isResizing = true;
        startX = e.clientX;
        const sidebar = document.getElementById("sidebar");
        startWidth = sidebar.offsetWidth;
        document.body.style.cursor = "col-resize";
        document.body.style.userSelect = "none";
        handle.classList.add("active");

        document.addEventListener("mousemove", onMouseMove);
        document.addEventListener("mouseup", onMouseUp);
    });

    function onMouseMove(e) {
        if (!isResizing) return;
        const dx = e.clientX - startX;
        let newWidth = startWidth + dx;
        const sidebar = document.getElementById("sidebar");
        const minWidth = 200;
        const maxWidth = 400;
        if (newWidth < minWidth) newWidth = minWidth;
        if (newWidth > maxWidth) newWidth = maxWidth;
        sidebar.style.width = newWidth + "px";
    }

    function onMouseUp() {
        isResizing = false;
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
        const handle = document.getElementById("sidebar-resize-handle");
        if (handle) handle.classList.remove("active");
        document.removeEventListener("mousemove", onMouseMove);
        document.removeEventListener("mouseup", onMouseUp);
    }
}

// ---------- PDF Upload ----------
async function uploadPDF() {
    const fileInput = document.getElementById("pdf-upload-input");
    if (!fileInput || !fileInput.files.length) return;

    const file = fileInput.files[0];
    if (!file.name.toLowerCase().endsWith(".pdf")) {
        alert("Only PDF files are allowed.");
        fileInput.value = "";
        return;
    }

    // Quick feedback
    const input = document.getElementById("user-question");
    if (input) input.placeholder = "Uploading PDF...";

    const formData = new FormData();
    formData.append("student_key", studentKey);
    formData.append("password", studentPassword);
    formData.append("file", file);

    try {
        const response = await fetch(`${API_BASE_URL}/upload-pdf`, {
            method: "POST",
            body: formData
        });
        const data = await response.json();
        if (data.success) {
            // Show confirmation as a system message
            const outputArea = document.getElementById("output-area");
            const msg = document.createElement("div");
            msg.className = "message-row system";
            msg.innerHTML = `<div class="message-bubble">📄 <strong>PDF uploaded:</strong> ${escapeHTML(data.filename)} (${data.characters_extracted} characters)<br>You can now ask questions about this document.</div>`;
            outputArea.appendChild(msg);
            scrollToBottom(true);
        } else {
            alert("PDF upload failed: " + (data.message || "Unknown error"));
        }
    } catch (error) {
        alert("Connection error during PDF upload: " + error.message);
    } finally {
        fileInput.value = "";
        if (input) input.placeholder = "Message CareerMind AI...";
    }
}

// ---------- Ask Smart Agent (STREAMING) ----------
async function askSmartAgent() {
    const input = document.getElementById("user-question");
    const sendButton = document.getElementById("send-button");
    const welcomeScreen = document.getElementById("welcome-screen");

    if (!input || !sendButton) return;

    const question = input.value.trim();
    if (!question) return;

    if (!studentKey || !studentPassword) {
        appendAIMessage("Please sign in first.");
        return;
    }

    if (welcomeScreen) welcomeScreen.classList.add("hidden");

    input.value = "";
    input.style.height = "auto";
    sendButton.disabled = true;

    currentChatMessages.push({ type: "user", content: question });
    appendUserMessage(question);

    // Prepare AI message bubble (empty initially)
    const outputArea = document.getElementById("output-area");
    const msgDiv = document.createElement("div");
    msgDiv.className = "message-row ai fade-in";
    const contentId = `stream-content-${Date.now()}`;
    msgDiv.innerHTML = `
            <div class="message-bubble">
                <div class="message-sender">CareerMind AI</div>
                <div class="message-content" id="${contentId}">
                    <div class="typing-dots">
                        <span class="dot"></span><span class="dot"></span><span class="dot"></span>
                    </div>
                </div>
            </div>
        `;
    outputArea.appendChild(msgDiv);
    setTimeout(() => msgDiv.classList.remove("fade-in"), 400);
    scrollToBottom(true);

    const contentEl = document.getElementById(contentId);

    // Push AI message to history early so we can update it
    const aiMessageObj = { type: "ai", content: "", sources: [] };
    currentChatMessages.push(aiMessageObj);

    let fullAnswer = "";
    let isFirstToken = true;

    try {
        // 🔁 CALL THE NEW STREAMING ENDPOINT
        const response = await fetch(`${API_BASE_URL}/smart-chat-stream`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                student_key: studentKey,
                password: studentPassword,
                question: question
            })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            fullAnswer += chunk;

            if (isFirstToken && chunk.trim().length > 0) {
                contentEl.innerHTML = "";
                isFirstToken = false;
            }

            // Check for IMAGE_URL in the accumulated answer
            if (fullAnswer.includes("IMAGE_URL:")) {
                const parts = fullAnswer.split("IMAGE_URL:");
                let textPart = parts[0].trim();
                const urlPart = parts[1].trim();

                // Custom success message
                if (textPart.toLowerCase().includes("generated an image")) {
                    textPart = "Image generated successfully! Now you can download it.";
                }

                contentEl.innerText = textPart;

                // If the URL part is complete (or at least looks like a URL)
                if (urlPart.length > 5 && !contentEl.parentElement.querySelector(".generated-image-card")) {
                    const fullImageUrl = urlPart.startsWith("http") ? urlPart : `${API_BASE_URL}${urlPart}`;
                    const card = document.createElement("div");
                    card.className = "generated-image-card";
                    card.innerHTML = `
                        <div class="generated-image-wrapper">
                            <img src="${fullImageUrl}" alt="Generated image" class="generated-image">
                        </div>
                        <div class="image-actions">
                            <button onclick="downloadImage('${fullImageUrl}', 'careermind_image.png')" class="download-btn">
                                <i class="fa-solid fa-download"></i> Download Image
                            </button>
                        </div>
                    `;
                    contentEl.parentElement.appendChild(card);

                    // Update current history with the image URL (keep the relative one for storage)
                    const lastMsg = currentChatMessages[currentChatMessages.length - 1];
                    if (lastMsg && lastMsg.type === "ai") {
                        lastMsg.imageUrl = urlPart;
                        lastMsg.content = textPart;

                        // FORCE SAVE AND REFRESH SIDEBAR
                        saveChatHistories();
                        renderChatHistories();
                    }
                }
            } else {
                contentEl.appendChild(document.createTextNode(chunk));
            }

            scrollToBottom(true);
        }

        // Finalize the content in history
        if (fullAnswer.includes("IMAGE_URL:")) {
            const parts = fullAnswer.split("IMAGE_URL:");
            let textPart = parts[0].trim();
            if (textPart.toLowerCase().includes("generated an image")) {
                textPart = "Image generated successfully! Now you can download it.";
            }
            aiMessageObj.content = textPart;
            aiMessageObj.imageUrl = parts[1].trim();
        } else {
            aiMessageObj.content = fullAnswer;
        }

        saveChatHistories();

        // 🆕 AUTO-SAVE TO SIDEBAR: If this is a new chat, commit it to history list immediately
        if (!currentChatId && currentChatMessages.length >= 2) {
            const firstUserMsg = currentChatMessages.find(m => m.type === 'user');
            const title = firstUserMsg ? firstUserMsg.content.substring(0, 50) : "New chat";
            currentChatId = Date.now().toString();
            const newHistory = {
                id: currentChatId,
                title: title,
                messages: JSON.parse(JSON.stringify(currentChatMessages))
            };
            chatHistories.push(newHistory);
            saveChatHistories();
            renderHistoryList();
        } else if (currentChatId) {
            // Update existing history entry
            const chatIdx = chatHistories.findIndex(c => c.id === currentChatId);
            if (chatIdx !== -1) {
                chatHistories[chatIdx].messages = JSON.parse(JSON.stringify(currentChatMessages));
                saveChatHistories();
            }
        }
    } catch (error) {
        console.error("Streaming error:", error);

        // Only show error if we have NO content at all
        const hasContent = contentEl && (contentEl.innerText.trim().length > 0 || contentEl.parentElement.querySelector(".generated-image-card"));

        if (!hasContent) {
            if (contentEl) {
                msgDiv.remove();
                currentChatMessages.pop();
            }
            showError(document.getElementById("output-area"), "The connection was interrupted. Please try again.");
        } else {
            // We have content, so just finalize what we have instead of showing an error
            console.log("Stream interrupted but content exists. Finalizing normally.");
            if (fullAnswer.includes("IMAGE_URL:")) {
                const parts = fullAnswer.split("IMAGE_URL:");
                let textPart = parts[0].trim();
                if (textPart.toLowerCase().includes("generated an image")) {
                    textPart = "Image generated successfully! Now you can download it.";
                }
                aiMessageObj.content = textPart;
                aiMessageObj.imageUrl = parts[1].trim();
            } else {
                aiMessageObj.content = fullAnswer;
            }
            saveChatHistories();
        }
    } finally {
        sendButton.disabled = false;
        if (input) input.focus();
        scrollToBottom(true);
    }
}

// ---------- UI Helpers ----------
function setButtonLoading(btn, isLoading, text) {
    if (!btn) return;
    btn.disabled = isLoading;
    btn.innerHTML = isLoading ? `<i class="fa-solid fa-spinner fa-spin"></i> ${text}` : text;
}

function showError(el, msg) {
    if (!el) return;
    el.innerHTML = `<div class="animate-pop" style="color: var(--danger); background: rgba(239, 68, 68, 0.1); padding: 12px; border-radius: 12px; font-size: 0.9rem; margin-top: 16px; border: 1px solid rgba(239, 68, 68, 0.2);"><i class="fa-solid fa-circle-exclamation"></i> ${msg}</div>`;
}

function showSuccess(el, msg) {
    if (!el) return;
    el.innerHTML = `<div class="animate-pop" style="color: var(--success); background: rgba(16, 185, 129, 0.1); padding: 12px; border-radius: 12px; font-size: 0.9rem; margin-top: 16px; border: 1px solid rgba(16, 185, 129, 0.2);"><i class="fa-solid fa-circle-check"></i> ${msg}</div>`;
}

function escapeHTML(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}
