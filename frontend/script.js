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

const collegeOptions = {
    "Technology / Computer Science": {
        "BCA": [
            "Artificial Intelligence & Machine Learning",
            "Data Science",
            "Cybersecurity",
            "Cloud Computing",
            "Full Stack Development",
            "General BCA"
        ],
        "B.Tech": [
            "Computer Science Engineering",
            "Information Technology",
            "Artificial Intelligence",
            "Data Science",
            "Electronics & Communication"
        ],
        "B.Sc Computer Science": [
            "Software Development",
            "Network Security",
            "Data Analytics"
        ],
        "MCA": ["General MCA", "Cloud Computing", "AI & ML"],
        "M.Tech": ["CSE", "Data Science", "Cyber Security"]
    },
    "Commerce": {
        "B.Com": [
            "Accounting",
            "Finance",
            "Taxation",
            "Banking & Insurance",
            "Business Analytics"
        ],
        "BBA": [
            "Marketing",
            "Finance",
            "Human Resource",
            "International Business",
            "Business Analytics"
        ],
        "BMS": ["Management Studies", "Finance", "Marketing"],
        "MBA": ["Marketing", "Finance", "HR", "Operations", "IT"]
    },
    "Science": {
        "B.Sc": [
            "Physics",
            "Chemistry",
            "Mathematics",
            "Biology",
            "Biotechnology",
            "Computer Science"
        ],
        "B.Tech": ["Biotech Engineering", "Food Technology"],
        "MBBS": ["General Medicine"],
        "B.Pharm": ["Pharmacology", "Pharmaceutics"],
        "Nursing": ["General Nursing"]
    },
    "Arts / Humanities": {
        "BA": [
            "English",
            "History",
            "Political Science",
            "Psychology",
            "Sociology",
            "Economics"
        ],
        "BSW": ["Social Work"],
        "BJMC": ["Journalism", "Mass Communication"],
        "BFA": ["Fine Arts", "Painting", "Sculpture"]
    }
};

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
            const safeAnswer = typeof marked !== 'undefined' ? marked.parse(msg.content) : escapeHTML(msg.content);
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
    // sidebar resize initialization
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

let initialRegisterHTML = "";

function showRegister() {
    hideAllSections();
    const registerSection = document.getElementById("register-section");
    const authBox = registerSection.querySelector(".auth-box");

    // Remove success mode when returning to register form
    if (authBox) {
        authBox.classList.remove("success-mode");
    }

    // Save initial HTML once so we can restore it after success card
    if (!initialRegisterHTML && authBox) {
        initialRegisterHTML = authBox.innerHTML;
    }

    // Restore form if it was replaced by success card
    if (authBox && initialRegisterHTML && authBox.querySelector(".success-icon")) {
        authBox.innerHTML = initialRegisterHTML;
    }

    registerSection.classList.remove("hidden");
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
}

function hideAllSections() {
    const sections = [
        "register-section",
        "login-section",
        "student-type-section",
        "school-onboarding-section",
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


async function submitOnboarding() {
    const resultBox = document.getElementById("onboarding-result");
    const submitButton = document.getElementById("onboarding-submit");
    const fullName = document.getElementById("co-fullname").value.trim();
    let stream = document.getElementById("co-stream").value;
    let degree = document.getElementById("co-degree").value;
    const semester = document.getElementById("co-semester").value;
    let specialization = document.getElementById("co-specialization").value;
    const goal = document.getElementById("co-goal").value.trim();
    const skills = document.getElementById("co-skills").value.trim();

    // Use Other value if selected
    if (stream === "Other") {
        stream = document.getElementById("co-stream-other").value.trim() || "Other";
    }
    if (degree === "Other") {
        degree = document.getElementById("co-degree-other").value.trim() || "Other";
    }
    if (specialization === "Other") {
        specialization = document.getElementById("co-specialization-other").value.trim() || "Other";
    }

    if (!fullName || !stream || !degree || !semester || !specialization || !goal || !skills) {
        showError(resultBox, "Please fill in all required fields.");
        return;
    }

    const answers = [
        { question: "Full Name", answer: fullName },
        { question: "Stream", answer: stream },
        { question: "Degree / Course", answer: degree },
        { question: "Semester / Year", answer: semester },
        { question: "Specialization", answer: specialization },
        { question: "Primary Career Goal", answer: goal },
        { question: "Top Skills", answer: skills }
    ];

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

// ---------- NEW SCHOOL ONBOARDING LOGIC ----------

function showStudentTypeSelection(newStudentKey, newStudentPassword) {
    studentKeyOnboarding = newStudentKey;
    studentPasswordOnboarding = newStudentPassword;
    hideAllSections();
    document.getElementById("student-type-section").classList.remove("hidden");
}

async function selectStudentType(type) {
    try {
        const response = await fetch(`${API_BASE_URL}/set-student-type`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                student_key: studentKeyOnboarding,
                password: studentPasswordOnboarding,
                student_type: type
            })
        });
        const data = await response.json();
        if (data.success) {
            if (type === 'school') {
                showSchoolOnboarding(studentKeyOnboarding, studentPasswordOnboarding);
            } else {
                showOnboarding(studentKeyOnboarding, studentPasswordOnboarding);
            }
        } else {
            alert("Error setting student type: " + data.message);
        }
    } catch (error) {
        alert("Connection error setting student type.");
    }
}

function showSchoolOnboarding(key, password) {
    studentKeyOnboarding = key;
    studentPasswordOnboarding = password;
    hideAllSections();
    document.getElementById("school-onboarding-section").classList.remove("hidden");
    updateDynamicSkills(); // Initialize skills area
}

function goBackToSelection() {
    hideAllSections();
    document.getElementById("student-type-section").classList.remove("hidden");
}

function handleCollegeStreamChange() {
    const stream = document.getElementById("co-stream").value;
    const degreeSelect = document.getElementById("co-degree");
    const specSelect = document.getElementById("co-specialization");

    // Reset following dropdowns
    degreeSelect.innerHTML = '<option value="">Select Degree</option>';
    specSelect.innerHTML = '<option value="">Select Specialization (Select Degree first)</option>';
    degreeSelect.disabled = true;
    specSelect.disabled = true;

    toggleOtherInput('co-stream', 'co-stream-other');

    if (stream && stream !== "Other") {
        const degrees = Object.keys(collegeOptions[stream] || {});
        if (degrees.length > 0) {
            degrees.forEach(deg => {
                const opt = document.createElement("option");
                opt.value = deg;
                opt.textContent = deg;
                degreeSelect.appendChild(opt);
            });
            const otherOpt = document.createElement("option");
            otherOpt.value = "Other";
            otherOpt.textContent = "Other";
            degreeSelect.appendChild(otherOpt);
            degreeSelect.disabled = false;
        } else {
            // No predefined degrees, let them type Other
            degreeSelect.innerHTML = '<option value="Other">Other</option>';
            degreeSelect.disabled = false;
            degreeSelect.value = "Other";
            handleCollegeDegreeChange();
        }
    } else if (stream === "Other") {
        degreeSelect.innerHTML = '<option value="Other">Other</option>';
        degreeSelect.disabled = false;
        degreeSelect.value = "Other";
        handleCollegeDegreeChange();
    }
}

function handleCollegeDegreeChange() {
    const stream = document.getElementById("co-stream").value;
    const degree = document.getElementById("co-degree").value;
    const specSelect = document.getElementById("co-specialization");

    specSelect.innerHTML = '<option value="">Select Specialization</option>';
    specSelect.disabled = true;

    toggleOtherInput('co-degree', 'co-degree-other');

    if (stream && degree && stream !== "Other" && degree !== "Other") {
        const specializations = collegeOptions[stream][degree] || [];
        if (specializations.length > 0) {
            specializations.forEach(spec => {
                const opt = document.createElement("option");
                opt.value = spec;
                opt.textContent = spec;
                specSelect.appendChild(opt);
            });
            const otherOpt = document.createElement("option");
            otherOpt.value = "Other";
            otherOpt.textContent = "Other";
            specSelect.appendChild(otherOpt);
            specSelect.disabled = false;
        } else {
            specSelect.innerHTML = '<option value="Other">Other</option>';
            specSelect.disabled = false;
            specSelect.value = "Other";
            toggleOtherInput('co-specialization', 'co-specialization-other');
        }
    } else if (degree === "Other") {
        specSelect.innerHTML = '<option value="Other">Other</option>';
        specSelect.disabled = false;
        specSelect.value = "Other";
        toggleOtherInput('co-specialization', 'co-specialization-other');
    }
}

function toggleOtherInput(selectId, otherId) {
    const select = document.getElementById(selectId);
    const otherInput = document.getElementById(otherId);
    if (select && otherInput) {
        if (select.value === "Other") {
            otherInput.classList.remove("hidden");
            otherInput.focus();
        } else {
            otherInput.classList.add("hidden");
        }
    }
}

function handleStreamChange() {
    toggleOtherInput('so-stream', 'so-stream-other');
    updateDynamicSkills();
}

function updateDynamicSkills() {
    const stream = document.getElementById("so-stream").value;
    const container = document.getElementById("dynamic-skills-container");

    if (!stream) {
        container.innerHTML = '<span style="color: var(--text-muted); font-size: 0.85rem;">Please select a Stream/Interest Area first to see relevant skills.</span>';
        return;
    }

    const skillsMap = {
        "CSE/IT": ["Python", "Java", "C++", "Data Structures", "Web Development", "AI/ML", "Database", "Cybersecurity", "Cloud Computing"],
        "Commerce": ["Accounting", "Excel", "Business Studies", "Finance", "Marketing", "Tally", "Economics"],
        "Science": ["Physics", "Chemistry", "Biology", "Mathematics", "Research Skills", "Lab Techniques"],
        "Arts/Humanities": ["History", "Political Science", "Psychology", "Writing", "Communication", "Sociology"],
        "Management": ["Leadership", "Excel", "Presentation", "Business Analytics", "Public Speaking", "Teamwork"],
        "Other": ["Communication", "Problem Solving", "Time Management", "Critical Thinking", "Adaptability"]
    };

    const skills = skillsMap[stream] || skillsMap["Other"];

    container.innerHTML = skills.map((skill, index) => `
        <label class="skill-checkbox-label" style="display: flex; align-items: center; gap: 6px; background: #1c1c21; padding: 6px 12px; border-radius: 20px; font-size: 0.85rem; border: 1px solid var(--border); cursor: pointer; transition: all 0.2s;">
            <input type="checkbox" name="school_skills" value="${skill}" style="accent-color: var(--accent);">
            ${skill}
        </label>
    `).join("");
}

async function submitSchoolOnboarding() {
    const resultBox = document.getElementById("school-onboarding-result");
    const submitButton = document.getElementById("school-onboarding-submit");

    const fullName = document.getElementById("so-fullname").value.trim();
    let gradeClass = document.getElementById("so-grade").value;
    let board = document.getElementById("so-board").value;
    let stream = document.getElementById("so-stream").value;
    const goal = document.getElementById("so-goal").value.trim();
    const favSubjects = document.getElementById("so-fav-subjects").value.trim();
    const weakSubjects = document.getElementById("so-weak-subjects").value.trim();
    const skillLevel = document.getElementById("so-skill-level").value;
    const learningStyle = document.getElementById("so-learning-style").value;
    const futureTarget = document.getElementById("so-target").value;
    const notes = document.getElementById("so-notes").value.trim();

    // Use Other values if selected
    if (gradeClass === "Other") {
        gradeClass = document.getElementById("so-grade-other").value.trim() || "Other";
    }
    if (board === "Other") {
        board = document.getElementById("so-board-other").value.trim() || "Other";
    }
    if (stream === "Other") {
        stream = document.getElementById("so-stream-other").value.trim() || "Other";
    }

    // Get checked skills
    const skillCheckboxes = document.querySelectorAll('input[name="school_skills"]:checked');
    const selectedSkills = Array.from(skillCheckboxes).map(cb => cb.value).join(", ");

    if (!fullName || !gradeClass || !board || !stream || !goal || !favSubjects || !skillLevel || !learningStyle || !futureTarget) {
        showError(resultBox, "Please fill in all required fields.");
        return;
    }

    setButtonLoading(submitButton, true, "Saving...");
    resultBox.innerHTML = "";

    try {
        const response = await fetch(`${API_BASE_URL}/school-onboarding`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                student_key: studentKeyOnboarding,
                password: studentPasswordOnboarding,
                full_name: fullName,
                grade_class: gradeClass,
                board: board,
                stream_interest: stream,
                career_goal: goal,
                favorite_subjects: favSubjects,
                weak_subjects: weakSubjects,
                skills_interested: selectedSkills,
                current_skill_level: skillLevel,
                learning_style: learningStyle,
                future_target: futureTarget,
                notes: notes
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
            showError(resultBox, data.message || "Failed to save profile.");
        }
    } catch (error) {
        showError(resultBox, `Connection error: ${error.message}`);
    } finally {
        setButtonLoading(submitButton, false, "Save Profile");
    }
}


let resendTimer = null;
let resendSeconds = 60;
let isRegistering = false;

async function registerStudent() {
    if (isRegistering) return;

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

    isRegistering = true;
    setButtonLoading(button, true, "Creating account...");
    resultBox.innerHTML = "";

    // Cold start timeout UX
    const timeoutMsg = setTimeout(() => {
        if (isRegistering) {
            showSuccess(resultBox, "Server is starting. This may take a few moments...");
        }
    }, 15000);

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

        clearTimeout(timeoutMsg);
        const data = await response.json();

        if (data.registration && data.registration.success) {
            clearSession();
            studentFirstName = firstName;
            localStorage.setItem("student_first_name", studentFirstName);

            // Show Success Card
            showRegisterSuccessCard(email);
            safeClearRegistrationForm();
        } else {
            showError(resultBox, data.registration?.message || "Registration failed. Please try again.");
        }
    } catch (error) {
        clearTimeout(timeoutMsg);
        console.error("Registration error:", error);
        showError(resultBox, "Server connection failed. Please try again later.");
    } finally {
        isRegistering = false;
        setButtonLoading(button, false, "Create Account");
    }
}

function showRegisterSuccessCard(email) {
    const registerBox = document.querySelector("#register-section .auth-box");
    if (!registerBox) return;
    registerBox.classList.add("success-mode");
    const safeEmail = escapeHTML(email);

    registerBox.innerHTML = `
        <div class="brand-mark">CM</div>

        <div class="success-icon" style="font-size: 3rem; color: #10b981; margin-bottom: 20px;">
            <i class="fa-solid fa-circle-check"></i>
        </div>

        <h2>Account Created Successfully</h2>

        <p class="auth-subtitle" style="margin-bottom: 24px;">
            A verification email containing your Student Key has been sent to:
            <br><br>
            <strong style="color:#ffffff; font-size:15px;">${safeEmail}</strong>
            <br><br>
            Please check your inbox and spam folder before requesting a resend.
        </p>
        
        <div class="info-card" style="background: rgba(139, 92, 246, 0.05); padding: 15px; border-radius: 12px; margin-bottom: 24px; border: 1px solid rgba(139, 92, 246, 0.2); text-align: left;">
            <ul style="margin: 0; padding-left: 20px; font-size: 0.9rem; color: #94a3b8;">
                <li>Find your unique Student Key in the email</li>
                <li>Use it along with your password to sign in</li>
                <li>Complete your profile to unlock full potential</li>
            </ul>
        </div>

        <div id="resend-result"></div>

        <div class="register-success-actions">
            <button 
                type="button"
                id="resend-btn"
                class="btn-primary resend-student-key-btn"
                onclick="resendStudentKey('${safeEmail}')"
                disabled>
                Resend Student Key in 60s
            </button>

            <button 
                type="button"
                onclick="showLogin()"
                class="btn-primary go-signin-btn">
                Go to Sign In
            </button>
        </div>
        
        <div class="debanjan-footer" style="margin-top: 30px;">
            © 2026 Debanjan Mondal. All rights reserved.
        </div>
    `;

    startResendCountdown();
}

function startResendCountdown() {
    const btn = document.getElementById("resend-btn");
    if (!btn) return;

    clearInterval(resendTimer);

    resendSeconds = 60;

    btn.disabled = true;
    btn.innerHTML = `Resend Student Key in ${resendSeconds}s`;

    resendTimer = setInterval(() => {
        resendSeconds--;

        if (resendSeconds <= 0) {
            clearInterval(resendTimer);

            btn.disabled = false;
            btn.innerHTML = "Resend Student Key";

        } else {
            btn.innerHTML = `Resend Student Key in ${resendSeconds}s`;
        }

    }, 1000);
}

async function resendStudentKey(email) {
    const btn = document.getElementById("resend-btn");
    const resultBox = document.getElementById("resend-result");
    if (!btn || btn.disabled) return;

    setButtonLoading(btn, true, "Sending...");
    btn.classList.add("loading");
    resultBox.innerHTML = "";

    try {
        const response = await fetch(`${API_BASE_URL}/resend-student-key`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: email })
        });
        const data = await response.json();

        if (data.success) {
            showSuccess(resultBox, data.message);
            startResendCountdown();
        } else {
            showError(resultBox, data.message);
            if (data.remaining_seconds) {
                resendSeconds = data.remaining_seconds;
            }
        }
    } catch (error) {
        showError(resultBox, "Failed to connect to server.");
    } finally {
        btn.classList.remove("loading");
        if (resendSeconds > 0) {
            // Keep it disabled if countdown still running
        } else {
            setButtonLoading(btn, false, "Resend Student Key");
        }
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

            // Enforce onboarding check - Intelligent routing
            if (data.onboarding_completed === false) {
                if (data.student && data.student.student_type === 'school') {
                    showSuccess(resultBox, "Login successful. Continuing school profile...");
                    setTimeout(() => showSchoolOnboarding(studentKey, studentPassword), 500);
                } else if (data.student && data.student.student_type === 'college') {
                    showSuccess(resultBox, "Login successful. Continuing college profile...");
                    setTimeout(() => showOnboarding(studentKey, studentPassword), 500);
                } else {
                    showSuccess(resultBox, "Login successful. Please complete your profile first.");
                    setTimeout(() => showStudentTypeSelection(studentKey, studentPassword), 500);
                }
            } else {
                showSuccess(resultBox, "Login successful. Redirecting...");
                setTimeout(() => showDashboard(), 300);
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

    // Clear result boxes
    const resultBoxes = ["login-result", "register-result", "onboarding-result", "school-onboarding-result"];
    resultBoxes.forEach(id => {
        const box = document.getElementById(id);
        if (box) box.innerHTML = "";
    });

    // Clear all onboarding forms
    const forms = ["onboarding-form", "school-onboarding-form"];
    forms.forEach(formId => {
        const form = document.getElementById(formId);
        if (form) {
            form.reset();
            // Also hide any "Other" inputs
            const others = form.querySelectorAll('[id$="-other"]');
            others.forEach(o => o.style.display = "none");
        }
    });

    // Clear type selection cache if any
    const streamOther = document.getElementById("co-stream-other");
    if (streamOther) streamOther.style.display = "none";
    const degreeOther = document.getElementById("co-degree-other");
    if (degreeOther) degreeOther.style.display = "none";
    const specOther = document.getElementById("co-specialization-other");
    if (specOther) specOther.style.display = "none";
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
    const cleanText = cleanAnswerText(answer);
    const safeAnswer = typeof marked !== 'undefined' ? marked.parse(cleanText) : escapeHTML(cleanText);
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

    // Use the clean success message and format it with markdown
    const rawText = text.toLowerCase().includes("generated an image")
        ? "Image generated successfully! Now you can download it."
        : cleanAnswerText(text);
    const safeAnswer = typeof marked !== 'undefined' ? marked.parse(rawText) : escapeHTML(rawText);

    const sourcesHtml = renderSources(sources);

    msg.innerHTML = `
        <div class="message-bubble">
            <div class="message-sender">CareerMind AI</div>
            <div class="message-content">${safeAnswer}</div>
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

                contentEl.innerHTML = typeof marked !== 'undefined' ? marked.parse(textPart) : escapeHTML(textPart);

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
                contentEl.innerHTML = typeof marked !== 'undefined' ? marked.parse(fullAnswer) : escapeHTML(fullAnswer);
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
