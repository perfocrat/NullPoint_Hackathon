
/* =========================================================
   CAREERLENS - DASHBOARD
   ========================================================= */


/* =========================================================
   TEMPORARY ANALYSIS DATA

   This will eventually come from Flask.

   DO NOT build the dashboard around hardcoded HTML.
   The backend will simply replace this object.
   ========================================================= */

const demoAnalysisData = {

    score: 78,

    targetRole: "Backend Developer",

    scoreStatus: "Strong",

    explanation:
        "Your profile demonstrates strong technical evidence, but there are a few important gaps between your current experience and your target role.",


    /* ==================== SCORE BREAKDOWN ==================== */

    breakdown: {

        skillMatch: 82,

        projectEvidence: 78,

        projectQuality: 74,

        activity: 69,

        roleRequirements: 76

    },


    /* ==================== SKILLS ==================== */

    skills: [

        {
            name: "Python",
            status: "verified",
            evidence: "6 repositories"
        },

        {
            name: "SQL",
            status: "verified",
            evidence: "3 projects"
        },

        {
            name: "Flask",
            status: "supported",
            evidence: "2 projects"
        },

        {
            name: "Git",
            status: "verified",
            evidence: "Regular repository activity"
        },

        {
            name: "Docker",
            status: "unverified",
            evidence: "No observable evidence"
        }

    ],


    /* ==================== GAPS ==================== */

    gaps: [

        {
            priority: "High Priority",

            name: "Docker",

            description:
                "Your target role expects containerization experience, but there is currently no strong evidence of Docker usage.",

            action:
                "Containerize one existing project."
        },

        {
            priority: "High Priority",

            name: "REST APIs",

            description:
                "Backend roles typically require experience designing and consuming REST APIs.",

            action:
                "Build a Flask REST API."
        },

        {
            priority: "Medium Priority",

            name: "Testing",

            description:
                "Your profile has limited evidence of automated software testing.",

            action:
                "Add unit tests to an existing project."
        }

    ],


    /* ==================== ROLE FIT ==================== */

    roles: [

        {
            name: "Backend Developer",
            fit: 84,
            primary: true,
            description:
                "Strong alignment with your Python, SQL and Flask experience."
        },

        {
            name: "Python Developer",
            fit: 81,
            primary: false,
            description:
                "Your Python evidence makes this another strong career match."
        },

        {
            name: "Full Stack Developer",
            fit: 72,
            primary: false,
            description:
                "Good foundation, but frontend and deployment evidence can improve."
        }

    ],


    /* ==================== ROADMAP ==================== */

    roadmap: [

        {
            phase: "Phase 01",
            duration: "Week 1",
            title: "Build a REST API",

            description:
                "Learn REST principles and build a production-style API using Flask.",

            task:
                "Build a Flask REST API"
        },

        {
            phase: "Phase 02",
            duration: "Week 2",
            title: "Learn Docker",

            description:
                "Understand containers and package your existing project into a Docker image.",

            task:
                "Dockerize your project"
        },

        {
            phase: "Phase 03",
            duration: "Week 3",
            title: "Add Automated Testing",

            description:
                "Learn unit testing and add meaningful tests to your backend application.",

            task:
                "Write API tests"
        },

        {
            phase: "Phase 04",
            duration: "Week 4",
            title: "Deploy Your Application",

            description:
                "Deploy your project and create observable evidence of your deployment skills.",

            task:
                "Deploy the project"
        }

    ]

};

let analysisData = demoAnalysisData;
try {
    const savedAnalysis = sessionStorage.getItem("careerLensAnalysis");
    if (savedAnalysis) {
        const parsed = JSON.parse(savedAnalysis);
        const roleLabels = {
            "backend-developer": "Backend Developer",
            "frontend-developer": "Frontend Developer",
            "fullstack-developer": "Full Stack Developer",
            "data-scientist": "Data Scientist",
            "ml-engineer": "Machine Learning Engineer",
            "software-engineer": "Software Engineer"
        };
        analysisData = {
            ...demoAnalysisData,
            ...parsed,
            targetRole: roleLabels[parsed.targetRole] || parsed.targetRole || demoAnalysisData.targetRole,
            explanation: parsed.explanation || "Your profile has been evaluated against the evidence and requirements for this role.",
            breakdown: { ...demoAnalysisData.breakdown, ...(parsed.breakdown || {}) },
            skills: parsed.skills || demoAnalysisData.skills,
            gaps: parsed.gaps || demoAnalysisData.gaps,
            roles: parsed.roles || demoAnalysisData.roles,
            roadmap: parsed.roadmap || demoAnalysisData.roadmap
        };
    }
} catch (error) {
    console.warn("Could not load the latest CareerLens report.", error);
}


/* =========================================================
   ELEMENTS
   ========================================================= */

const readinessScore =
    document.getElementById("readinessScore");

const scoreRing =
    document.getElementById("scoreRing");

const targetRole =
    document.getElementById("targetRole");

const scoreExplanation =
    document.getElementById("scoreExplanation");

const skillsGrid =
    document.getElementById("skillsGrid");

const gapsGrid =
    document.getElementById("gapsGrid");

const roleGrid =
    document.getElementById("roleGrid");

const roadmap =
    document.getElementById("roadmap");

const newAnalysisButton =
    document.getElementById("newAnalysisButton");

const newAnalysisButtonBottom =
    document.getElementById("newAnalysisButtonBottom");

const printReportButton =
    document.getElementById("printReportButton");


/* =========================================================
   RENDER SCORE
   ========================================================= */

function renderScore(data) {

    const score = normalizePercent(data.score);

    readinessScore.textContent = score;

    targetRole.textContent =
        data.targetRole;

    scoreExplanation.textContent =
        data.explanation;

    const statusLabel = document.querySelector(".score-status");
    if (statusLabel && data.scoreStatus) statusLabel.textContent = data.scoreStatus;

    const breakdownValues = [
        data.breakdown.skillMatch,
        data.breakdown.projectEvidence,
        data.breakdown.projectQuality,
        data.breakdown.activity,
        data.breakdown.roleRequirements
    ];
    document.querySelectorAll(".breakdown-item").forEach((item, index) => {
        const value = Number(breakdownValues[index]);
        if (!Number.isFinite(value)) return;
        const safeValue = Math.max(0, Math.min(100, value));
        const label = item.querySelector(".breakdown-info strong");
        const bar = item.querySelector(".mini-progress-fill");
        if (label) label.textContent = `${safeValue}%`;
        if (bar) bar.style.width = `${safeValue}%`;
    });


    /*
        Circle circumference:

        2 × π × 76 ≈ 477.5
    */

    const circumference = 477.5;

    const offset =
        circumference -
        (score / 100) * circumference;

    document.querySelector(".score-circle").setAttribute(
        "aria-label",
        `Job readiness score: ${score} out of 100`
    );


    /*
        Small timeout allows the browser
        to animate the ring.
    */

    setTimeout(() => {

        scoreRing.style.strokeDashoffset =
            offset;

    }, 150);

}


/* =========================================================
   RENDER SKILLS
   ========================================================= */

function renderSkills(skills) {

    skillsGrid.innerHTML = "";
    document.getElementById("skillsSummary").textContent =
        `${skills.length} ${skills.length === 1 ? "skill" : "skills"} analyzed`;


    skills.forEach(skill => {

        const card =
            document.createElement("article");

        card.className =
            "skill-card";

        const status = ["verified", "supported", "unverified"].includes(skill.status)
            ? skill.status
            : "unknown";

        const statusText =
            getSkillStatusText(
                status
            );


        card.innerHTML = `

            <div class="skill-card-header">

                <span class="skill-name">
                    ${escapeHTML(skill.name)}
                </span>

                <span
                    class="skill-status ${status}"
                ></span>

            </div>


            <span
                class="skill-card-status ${status}"
            >
                ${statusText}
            </span>


            <p class="skill-evidence">
                ${escapeHTML(skill.evidence)}
            </p>

        `;


        skillsGrid.appendChild(card);

    });

}


/* =========================================================
   SKILL STATUS TEXT
   ========================================================= */

function getSkillStatusText(status) {

    switch (status) {

        case "verified":
            return "VERIFIED";

        case "supported":
            return "SUPPORTED";

        case "unverified":
            return "UNVERIFIED";

        default:
            return "UNKNOWN";

    }

}


/* =========================================================
   RENDER GAPS
   ========================================================= */

function renderGaps(gaps) {

    gapsGrid.innerHTML = "";
    const priorityGaps = gaps.filter(gap =>
        /high/i.test(String(gap.priority))
    ).length;
    document.getElementById("gapsSummary").textContent =
        `${priorityGaps} priority ${priorityGaps === 1 ? "gap" : "gaps"}`;


    gaps.forEach(gap => {

        const card =
            document.createElement("article");

        card.className =
            "gap-card";


        card.innerHTML = `

            <span class="gap-priority">
                ${escapeHTML(gap.priority)}
            </span>


            <h3>
                ${escapeHTML(gap.name)}
            </h3>


            <p>
                ${escapeHTML(gap.description)}
            </p>


            <span class="gap-action">
                Next step → ${escapeHTML(gap.action)}
            </span>

        `;


        gapsGrid.appendChild(card);

    });

}


/* =========================================================
   RENDER ROLES
   ========================================================= */

function renderRoles(roles) {

    roleGrid.innerHTML = "";


    roles.forEach(role => {

        const card =
            document.createElement("article");

        card.className =
            "role-card";

        const fit = normalizePercent(role.fit);

        if (role.primary) {

            card.classList.add(
                "primary-role"
            );

        }


        card.innerHTML = `

            <div class="role-card-header">

                <h3>
                    ${escapeHTML(role.name)}
                </h3>

                <span class="role-fit">
                    ${fit}%
                </span>

            </div>


            <div class="role-bar">

                <div
                    class="role-bar-fill"
                    style="width: ${fit}%"
                ></div>

            </div>


            <p class="role-description">
                ${escapeHTML(role.description)}
            </p>

        `;


        roleGrid.appendChild(card);

    });

}


/* =========================================================
   RENDER ROADMAP
   ========================================================= */

function renderRoadmap(roadmapData) {

    roadmap.innerHTML = "";
    document.getElementById("roadmapSummary").textContent =
        `${roadmapData.length} ${roadmapData.length === 1 ? "phase" : "phases"}`;


    roadmapData.forEach(
        (item, index) => {

            const element =
                document.createElement("div");

            element.className =
                "roadmap-item";


            element.innerHTML = `

                <div class="roadmap-number">
                    ${index + 1}
                </div>


                <div class="roadmap-content">

                    <div class="roadmap-meta">

                        <span class="roadmap-phase">
                            ${escapeHTML(item.phase)}
                        </span>

                        <span class="roadmap-duration">
                            ${escapeHTML(item.duration)}
                        </span>

                    </div>


                    <h3>
                        ${escapeHTML(item.title)}
                    </h3>


                    <p>
                        ${escapeHTML(item.description)}
                    </p>


                    <span class="roadmap-task">
                        ${escapeHTML(item.task)}
                    </span>

                </div>

            `;


            roadmap.appendChild(element);

        }
    );

}


/* =========================================================
   NEW ANALYSIS
   ========================================================= */

function startNewAnalysis() {

    window.location.href =
        "input.html";

}

function normalizePercent(value) {
    const number = Number(value);
    return Number.isFinite(number)
        ? Math.round(Math.max(0, Math.min(100, number)))
        : 0;
}


newAnalysisButton.addEventListener(
    "click",
    startNewAnalysis
);

newAnalysisButtonBottom.addEventListener(
    "click",
    startNewAnalysis
);

printReportButton.addEventListener(
    "click",
    () => window.print()
);


/* =========================================================
   HTML ESCAPING
   ========================================================= */

function escapeHTML(value) {

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

}


/* =========================================================
   INITIALIZE DASHBOARD
   ========================================================= */

function initializeDashboard() {

    renderScore(analysisData);

    renderSkills(
        analysisData.skills
    );

    renderGaps(
        analysisData.gaps
    );

    renderRoles(
        analysisData.roles
    );

    renderRoadmap(
        analysisData.roadmap
    );

}


/* Start dashboard */

initializeDashboard();
