
/* =========================================================
   CAREERLENS - DASHBOARD
   ========================================================= */


/* =========================================================
   TEMPORARY ANALYSIS DATA

   This will eventually come from Flask.

   DO NOT build the dashboard around hardcoded HTML.
   The backend will simply replace this object.
   ========================================================= */
const storedAnalysis =
    sessionStorage.getItem("careerLensAnalysis");

if (!storedAnalysis) {
    alert("No analysis data found. Please run a new analysis.");
    window.location.href = "input.html";
}

const rawAnalysis = JSON.parse(storedAnalysis);

console.log(
    "Real CareerLens analysis:",
    rawAnalysis
);

function buildDashboardData(data) {

    const metrics = data.metrics || {};

    // Convert backend metric objects into percentages
    const getMetric = (name) => {

        const metric = metrics[name];

        if (!metric) return 0;

        if (typeof metric === "number") {
            return Math.round(metric * 100);
        }

        if (typeof metric.value === "number") {
            return Math.round(metric.value * 100);
        }

        return 0;
    };


    // Calculate overall readiness
    const metricValues = [
        getMetric("consistency"),
        getMetric("tech_depth"),
        getMetric("frameworks"),
        getMetric("breadth"),
        getMetric("integrity"),
        getMetric("products"),
        getMetric("deployment"),
        getMetric("collaboration"),
        getMetric("documentation"),
        getMetric("proximity"),
        getMetric("gap"),
        getMetric("ecosystem")
    ];

    const validMetrics = metricValues.filter(value => value > 0);

    const score = validMetrics.length
        ? Math.round(
            validMetrics.reduce((sum, value) => sum + value, 0)
            / validMetrics.length
        )
        : 0;


    // Verified skills
    const skills = (data.verified_skills || []).map(skill => ({
        name: skill,
        status: "verified",
        evidence: "Verified through GitHub evidence"
    }));


    // Unverified claims
    const gaps = (data.unverified_claims || []).map(skill => ({
        priority: data.missing_track_skills?.includes(skill)
            ? "High Priority"
            : "Medium Priority",

        name: skill,

        description:
            `Your resume claims ${skill}, but the available GitHub evidence does not currently verify it.`,

        action:
            `Add a project demonstrating ${skill}.`
    }));


    return {

        score: score,

        targetRole: data.track,

        scoreStatus:
            score >= 75
                ? "Strong"
                : score >= 50
                    ? "Developing"
                    : "Needs Improvement",

        breakdown: {
            skillMatch: getMetric("integrity"),
            projectEvidence: getMetric("products"),
            projectQuality: getMetric("documentation"),
            activity: getMetric("consistency"),
            roleRequirements: getMetric("proximity")
        },

        skills: skills,

        gaps: gaps,

        roles: [
            {
                name: data.track,
                fit: score,
                primary: true,
                description:
                    `Your current profile alignment with ${data.track}.`
            }
        ],

        roadmap: (data.missing_track_skills || []).map(
            (skill, index) => ({
                phase: `Phase ${String(index + 1).padStart(2, "0")}`,
                duration: `Week ${index + 1}`,
                title: `Build ${skill} evidence`,
                description:
                    `Strengthen your ${skill} experience with a practical project.`,
                task:
                    `Create a project demonstrating ${skill}.`
            })
        )
    };
}


const analysisData = buildDashboardData(rawAnalysis);

console.log(
    "Dashboard data:",
    analysisData
);

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


/* =========================================================
   RENDER SCORE
   ========================================================= */

function renderScore(data) {

    readinessScore.textContent =
        data.score;

    targetRole.textContent =
        data.targetRole;

    scoreExplanation.textContent =
        data.explanation;


    /*
        Circle circumference:

        2 × π × 76 ≈ 477.5
    */

    const circumference = 477.5;

    const offset =
        circumference -
        (data.score / 100) * circumference;


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


    skills.forEach(skill => {

        const card =
            document.createElement("article");

        card.className =
            "skill-card";


        const statusText =
            getSkillStatusText(
                skill.status
            );


        card.innerHTML = `

            <div class="skill-card-header">

                <span class="skill-name">
                    ${escapeHTML(skill.name)}
                </span>

                <span
                    class="skill-status ${skill.status}"
                ></span>

            </div>


            <span
                class="skill-card-status ${skill.status}"
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
                    ${role.fit}%
                </span>

            </div>


            <div class="role-bar">

                <div
                    class="role-bar-fill"
                    style="width: ${role.fit}%"
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


newAnalysisButton.addEventListener(
    "click",
    startNewAnalysis
);

newAnalysisButtonBottom.addEventListener(
    "click",
    startNewAnalysis
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
