
/* =========================================================
   CAREERLENS - ANALYSIS LOADING
   ========================================================= */


/* ==================== ELEMENTS ==================== */

const progressFill =
    document.getElementById("progressFill");

const progressPercentage =
    document.getElementById("progressPercentage");

const progressBar =
    document.querySelector(".progress-bar");

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

    progressBar.setAttribute("aria-valuenow", progress);

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


/* ==================== RUN ANALYSIS ==================== */

async function runAnalysis() {

    if (!sessionStorage.getItem("careerLensAnalysis")) {
        window.location.replace("input.html");
        return;
    }

    for (
        let i = 0;
        i < analysisStages.length - 1;
        i++
    ) {

        const stage =
            analysisStages[i];


        updateProgress(
            stage.progress,
            stage.message
        );


        updateStep(i);


        /*
            Temporary simulation.

            Later this delay will be replaced
            by actual Flask API calls.
        */

        await new Promise(resolve => {

            setTimeout(
                resolve,
                1000
            );

        });

    }


    /* Final stage */

    const finalStage =
        analysisStages[
            analysisStages.length - 1
        ];


    updateProgress(
        finalStage.progress,
        finalStage.message
    );


    /*
        Mark all steps as complete.
    */

    analysisSteps.forEach(step => {

        step.classList.remove("active");

        step.classList.add("completed");

        step.querySelector(
            ".status-icon"
        ).textContent = "✓";

    });


    /*
        Small delay before dashboard.

        This gives the user time to see
        "Analysis complete".
    */

    await new Promise(resolve => {

        setTimeout(
            resolve,
            800
        );

    });


    /*
        TEMPORARY:

        Go to dashboard.

        Once Flask is connected,
        this page will only redirect
        after the real analysis succeeds.
    */

    window.location.href =
        "dashboard.html";

}


/* ==================== START ==================== */

runAnalysis();
