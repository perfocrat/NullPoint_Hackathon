
/* =========================================================
   CAREERLENS - DASHBOARD
   ========================================================= */


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

const breakdownList =
    document.getElementById("breakdownList");

const scoreStatus =
    document.getElementById("scoreStatus");

const scoreHeadline =
    document.getElementById("scoreHeadline");

const skillCount =
    document.getElementById("skillCount");

const gapCount =
    document.getElementById("gapCount");

const roadmapCount =
    document.getElementById("roadmapCount");

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

    scoreStatus.textContent =
        data.scoreStatus;

    scoreHeadline.textContent =
        data.headline;


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
   RENDER BREAKDOWN
   ========================================================= */

const BREAKDOWN_LABELS = {

    skillMatch: "Skill Match",

    projectEvidence: "Project Evidence",

    projectQuality: "Project Quality",

    activity: "Activity",

    roleRequirements: "Role Requirements"

};


function renderBreakdown(breakdown) {

    breakdownList.innerHTML = "";


    Object.keys(BREAKDOWN_LABELS).forEach(key => {

        const value = Number(breakdown[key]) || 0;

        const item =
            document.createElement("div");

        item.className = "breakdown-item";

        item.innerHTML = `

            <div class="breakdown-info">

                <span>
                    ${BREAKDOWN_LABELS[key]}
                </span>

                <strong>
                    ${value}%
                </strong>

            </div>

            <div class="mini-progress">

                <div
                    class="mini-progress-fill"
                    style="width: ${value}%"
                ></div>

            </div>

        `;

        breakdownList.appendChild(item);

    });

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

function plural(count, word) {

    return `${count} ${word}${count === 1 ? "" : "s"}`;

}


function showLoadError(message) {

    document.querySelector(".dashboard").innerHTML = `

        <section class="dashboard-section">

            <h2>We couldn't load your results.</h2>

            <p>${escapeHTML(message)}</p>

            <br>

            <a class="primary-button" href="input.html">
                Start a new analysis
            </a>

        </section>

    `;

}


async function initializeDashboard() {

    const jobId = getJobId();

    if (!jobId) {

        window.location.href = "input.html";

        return;

    }


    let analysisData;

    try {

        analysisData = await fetchResult(jobId);

    } catch (error) {

        showLoadError(error.message);

        return;

    }


    renderScore(analysisData);

    renderBreakdown(analysisData.breakdown);

    renderSkills(analysisData.skills);

    renderGaps(analysisData.gaps);

    renderRoles(analysisData.roles);

    renderRoadmap(analysisData.roadmap);


    skillCount.textContent =
        `${plural(analysisData.skills.length, "skill")} analyzed`;

    gapCount.textContent =
        `${plural(analysisData.gaps.length, "gap")} found`;

    roadmapCount.textContent =
        plural(analysisData.roadmap.length, "phase");

}


/* Start dashboard */

initializeDashboard();
