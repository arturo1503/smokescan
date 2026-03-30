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
    const finalizeStep = document.getElementById("finalize-step");
    const finalizeBtn = document.getElementById("finalize-btn");
    const resultsAside = document.getElementById("dashboard");
    const processingBox = document.getElementById("processing-box");

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
            await aiReply("Perfecto, trabajemos en **" + projectName + "**.");
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
                await aiReply("He detectado " + r2Followups.length + " puntos que necesitan m\u00e1s profundidad. Vamos uno por uno.");
                askNextR2();
            }
        } catch (e) {
            setTyping(false);
            await aiReply("Ha ocurrido un error al analizar. Pasemos al diagn\u00f3stico.");
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
            await aiReply(intro + "\n\n**" + pending.pregunta + "**");
        } else {
            await aiReply("Gracias. He perforado lo suficiente. Generemos el reporte.");
            showFinalize();
        }
    }

    // --- UI HELPERS ---
    function addMessage(role, text) {
        const div = document.createElement("div");
        const formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
        
        if (role === 'ai') {
            div.className = "ai-message";
            let stepTitle = currentStep > 0 ? "Step " + currentStep + ": " + (currentStep <= 7 ? "Contextual Analysis" : "Deep Drill") : "Initialization";
            div.innerHTML = `
                <div class="ai-icon-box">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path></svg>
                </div>
                <div class="ai-card">
                    <h4>${stepTitle}</h4>
                    <p>${formattedText}</p>
                </div>
            `;
        } else {
            div.className = "user-message";
            div.innerHTML = `
                <div class="user-card">${formattedText}</div>
                <div class="user-icon-box">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                </div>
            `;
        }
        
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
        if (processingBox) {
            if (val) {
                processingBox.classList.remove("hidden");
                chatHistory.appendChild(processingBox); // Move to bottom
            } else {
                processingBox.classList.add("hidden");
            }
        }
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function showFinalize() {
        const inputArea = document.querySelector(".input-area");
        if (inputArea) inputArea.style.display = "none";
        if (finalizeStep) finalizeStep.classList.remove("hidden");
        currentStep = 9;
    }

    function renderSidebar() {
        // Map 14 steps to the 5 visual steps
        let activeBadge = 1;
        if (currentStep > 2) activeBadge = 2;
        if (currentStep > 5) activeBadge = 3;
        if (currentStep > 8) activeBadge = 4;
        if (currentStep > 11) activeBadge = 5;
        
        for (let i = 1; i <= 5; i++) {
            const stepEl = document.getElementById("step-" + i);
            if (stepEl) {
                if (i <= activeBadge) stepEl.classList.add("active");
                else stepEl.classList.remove("active");
            }
        }
    }

    // --- FINALIZE ---
    finalizeBtn.addEventListener("click", async () => {
        finalizeBtn.textContent = "GENERATING REPORT...";
        finalizeBtn.disabled = true;

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
            if (data.error) {
                alert("Error del servidor: " + data.error);
            } else {
                document.querySelector(".chat-container").style.display = "none";
                if (resultsAside) {
                    resultsAside.style.display = "block";
                    resultsAside.classList.remove("hidden");
                }
                updateDashboard(data);
            }
        } catch (e) {
            alert("Error de conexi\u00f3n con el servidor.");
        } finally {
            finalizeBtn.textContent = "VER DIAGNÓSTICO FINAL";
            finalizeBtn.disabled = false;
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
                const textEl = document.getElementById("val-" + key);
                const barEl = document.getElementById("bar-" + key);
                if (textEl) textEl.textContent = val + "/10";
                if (barEl) barEl.style.width = (val * 10) + "%";
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
        document.getElementById("investment-estimate").textContent = data.investment_estimate || "--";
        document.getElementById("cash-flow-projection").textContent = data.cash_flow_projection || "--";
    }
});
