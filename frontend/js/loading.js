
/* =========================================================
   CAREERLENS - ANALYSIS LOADING
   ========================================================= */


/* ==================== ELEMENTS ==================== */

const progressFill =
    document.getElementById("progressFill");

const progressPercentage =
    document.getElementById("progressPercentage");

const loadingMessage =
    document.getElementById("loadingMessage");

const analysisSteps =
    document.querySelectorAll(".analysis-step");


/* ==================== ANALYSIS DATA ==================== */

const analysisStages = [

    {
        progress: 15,

        message:
            "Extracting information from your resume."
    },

    {
        progress: 35,

        message:
            "Collecting evidence from your profile."
    },

    {
        progress: 55,

        message:
            "Verifying your claimed skills."
    },

    {
        progress: 75,

        message:
            "Evaluating your fit for the target role."
    },

    {
        progress: 90,

        message:
            "Building your personalized roadmap."
    },

    {
        progress: 100,

        message:
            "Analysis complete."
    }

];


/* ==================== UPDATE PROGRESS ==================== */

function updateProgress(progress, message) {

    progressFill.style.width =
        `${progress}%`;

    progressPercentage.textContent =
        `${progress}%`;

    loadingMessage.textContent =
        message;

}


/* ==================== UPDATE STEP ==================== */

function updateStep(index) {

    analysisSteps.forEach(
        (step, stepIndex) => {

            const icon =
                step.querySelector(".status-icon");


            /*
                Previous steps
                become completed.
            */

            if (stepIndex < index) {

                step.classList.remove("active");

                step.classList.add("completed");

                icon.textContent = "✓";

            }


            /*
                Current step
                becomes active.
            */

            else if (stepIndex === index) {

                step.classList.add("active");

                step.classList.remove("completed");

                icon.textContent = "•";

            }


            /*
                Future steps
                remain inactive.
            */

            else {

                step.classList.remove("active");

                step.classList.remove("completed");

                icon.textContent = "○";

            }

        }
    );

}


/* ==================== SHOW FAILURE ==================== */

function showFailure(message) {

    updateProgress(0, message);

    document.querySelector(".loading-heading h1").textContent =
        "We couldn't finish the analysis.";

    document.querySelector(".loading-footnote").innerHTML =
        '<a class="secondary-button" href="input.html">Go back and try again</a>';

    analysisSteps.forEach(step => {

        step.classList.remove("active");

    });

}


/* ==================== WAIT FOR BACKEND ==================== */

const POLL_INTERVAL_MS = 700;

function sleep(ms) {

    return new Promise(resolve => setTimeout(resolve, ms));

}


async function runAnalysis() {

    const jobId = getJobId();

    if (!jobId) {

        window.location.href = "input.html";

        return;

    }


    while (true) {

        let status;

        try {

            status = await fetchStatus(jobId);

        } catch (error) {

            showFailure(error.message);

            return;

        }


        if (status.status === "error") {

            showFailure(status.error);

            return;

        }


        if (status.status === "done") {

            break;

        }


        /*
            The backend reports which stage it is in
            (0-4). Show that stage as active.
        */

        const stage = Math.min(status.stage, analysisStages.length - 2);

        updateProgress(
            analysisStages[stage].progress,
            analysisStages[stage].message
        );

        updateStep(stage);

        await sleep(POLL_INTERVAL_MS);

    }


    /* Final stage */

    const finalStage =
        analysisStages[analysisStages.length - 1];

    updateProgress(
        finalStage.progress,
        finalStage.message
    );

    analysisSteps.forEach(step => {

        step.classList.remove("active");

        step.classList.add("completed");

        step.querySelector(".status-icon").textContent = "✓";

    });


    /* Let the user see "Analysis complete" */

    await sleep(800);

    window.location.href = "dashboard.html";

}


/* ==================== START ==================== */

runAnalysis();
