document.addEventListener("DOMContentLoaded", () => {
    // --- STATE ---
    let currentStep = 0;
    let r1Questions = [];
    let r1Answers = ["", "", "", "", "", "", ""];
    let r2Followups = [];
    let projectName = "";
    let isTyping = false;

    // --- ELEMENTS ---
    const chatHistory = document.getElementById("chat-history");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const typingIndicator = document.getElementById("typing-indicator");
    const finalizeStep = document.getElementById("finalize-step");
    const finalizeBtn = document.getElementById("finalize-btn");
    const resultsAside = document.getElementById("dashboard");
    const loadingOverlay = document.getElementById("loading-overlay");
    const evidenceChain = document.getElementById("evidence-chain");
    const roundTag = document.getElementById("round-tag");

    // --- INIT ---
    fetch("/api/questions/r1")
        .then(r => r.json())
        .then(data => {
            r1Questions = data;
            renderSidebar();
        });

    userInput.focus();

    // --- INTERACTION ---
    sendBtn.addEventListener("click", handleSend);
    userInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });

    function handleSend() {
        const text = userInput.value.trim();
        if (!text || isTyping) return;
        addMessage("user", text);
        userInput.value = "";
        processStep(text);
    }

    async function processStep(text) {
        if (currentStep === 0) {
            projectName = text;
            currentStep = 1;
            await aiReply(`Perfecto, trabajemos en **${projectName}**.`);
            askNextR1();
        } else if (currentStep >= 1 && currentStep <= 7) {
            r1Answers[currentStep - 1] = text;
            renderSidebar();
            if (currentStep < 7) {
                currentStep++;
                askNextR1();
            } else {
                currentStep = 8;
                await aiReply("Entendido. Dame un momento para analizar tus respuestas... estoy buscando puntos ciegos.");
                analyzeR1();
            }
        } else if (currentStep === 8) {
            const activeIdx = r2Followups.findIndex(f => f.answer === "");
            if (activeIdx !== -1) {
                r2Followups[activeIdx].answer = text;
                askNextR2();
            }
        }
    }

    // --- AI REPLIES ---
    async function askNextR1() {
        const q = r1Questions[currentStep - 1];
        roundTag.textContent = `RONDA 1: PREGUNTA ${currentStep}/7`;
        await aiReply(q.q);
    }

    async function analyzeR1() {
        setTyping(true);
        try {
            const res = await fetch("/api/analyze_r1", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ answers: r1Answers })
            });
            const data = await res.json();
            r2Followups = data.followups.map(f => ({ ...f, answer: "" }));
            setTyping(false);
            if (r2Followups.length === 0) {
                await aiReply("Excelente. No he detectado inconsistencias graves. Estamos listos para el diagn\u00f3stico final.");
                showFinalize();
            } else {
                roundTag.textContent = "RONDA 2: PERFORACI\u00d3N";
                await aiReply(`He detectado ${r2Followups.length} puntos que necesitan m\u00e1s profundidad. Vamos uno por uno.`);
                askNextR2();
            }
        } catch (e) {
            setTyping(false);
            showFinalize();
        }
    }

    async function askNextR2() {
        const pending = r2Followups.find(f => f.answer === "");
        if (pending) {
            let intro = "";
            if (pending.razon === "superficial") intro = "Esta respuesta me parece un poco superficial:";
            else if (pending.razon === "contradiccion") intro = "He notado una posible contradicci\u00f3n aqu\u00ed:";
            else intro = "Necesito m\u00e1s evidencia sobre esto:";
            await aiReply(`${intro}\n\n**${pending.pregunta}**`);
        } else {
            await aiReply("Gracias. He perforado lo suficiente. Generemos el reporte.");
            showFinalize();
        }
    }

    // --- UI HELPERS ---
    function addMessage(role, text) {
        const div = document.createElement("div");
        div.className = `${role}-bubble`;
        div.innerHTML = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
        chatHistory.appendChild(div);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    async function aiReply(text) {
        setTyping(true);
        const delay = Math.min(1500, 500 + text.length * 10);
        await new Promise(r => setTimeout(r, delay));
        setTyping(false);
        addMessage("ai", text);
    }

    function setTyping(val) {
        isTyping = val;
        if (val) typingIndicator.classList.remove("hidden");
        else typingIndicator.classList.add("hidden");
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function showFinalize() {
        document.getElementById("chat-input-area")?.classList.add("hidden");
        finalizeStep.classList.remove("hidden");
        currentStep = 9;
    }

    function renderSidebar() {
        evidenceChain.innerHTML = "";
        r1Questions.forEach((q, i) => {
            const step = document.createElement("div");
            const isCompleted = r1Answers[i] !== "";
            const isActive = (i === currentStep - 1);
            step.className = `chain-step ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`;
            step.innerHTML = `
                <div class="step-num">${i + 1}</div>
                <div class="step-label">${q.q.substring(0, 20)}...</div>
            `;
            evidenceChain.appendChild(step);
        });
    }

    // --- FINALIZE ---
    finalizeBtn.addEventListener("click", async () => {
        loadingOverlay.classList.remove("hidden");
        const payload = {
            projectName,
            answers_r1: r1Answers,
            answers_r2: r2Followups.filter(f => f.answer !== "")
        };
        try {
            const res = await fetch("/api/validate", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            updateDashboard(data);
            document.getElementById("wizard-panel").classList.add("hidden");
            resultsAside.style.display = "block";
        } catch (e) {
            alert("Error");
        } finally {
            loadingOverlay.classList.add("hidden");
        }
    });

    function updateDashboard(data) {
        document.getElementById("validation-score").textContent = data.score || "--";
        document.getElementById("risk-percentage").textContent = (data.risk || "--") + "%";
        document.getElementById("market-potential").textContent = data.marketText || "--";
        document.getElementById("market-stars").innerHTML = data.stars || "";
        document.getElementById("tech-feasibility").textContent = data.techText || "--";
        document.getElementById("tech-status").textContent = data.techStatusText || "-";
        document.getElementById("competition-level").textContent = data.competitionText || "--";
        if (data.rubric) {
            Object.keys(data.rubric).forEach(key => {
                const val = data.rubric[key];
                const textEl = document.getElementById(`val-${key}`);
                const barEl = document.getElementById(`bar-${key}`);
                if (textEl) textEl.textContent = `${val}/10`;
                if (barEl) barEl.style.width = `${val * 10}%`;
            });
        }
        const mList = document.getElementById("mitigation-list");
        mList.innerHTML = "";
        (data.mitigation_advice || []).forEach(a => {
            const li = document.createElement("li");
            li.textContent = a;
            mList.appendChild(li);
        });
        document.getElementById("mitigation-card").classList.remove("hidden");
        if(data.scenarios) {
            document.getElementById("scenario-opt").textContent = data.scenarios.optimistic;
            document.getElementById("scenario-neu").textContent = data.scenarios.neutral;
            document.getElementById("scenario-pes").textContent = data.scenarios.pessimistic;
        }
        document.getElementById("investment-estimate").textContent = data.investment_estimate;
        document.getElementById("cash-flow-projection").textContent = data.cash_flow_projection;
    }
});
