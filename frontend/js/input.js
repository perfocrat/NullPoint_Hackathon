
/* =========================================================
   CAREERLENS - PROFILE INPUT
   ========================================================= */


/* ==================== ELEMENTS ==================== */

const form = document.getElementById("profileForm");

const resumeInput = document.getElementById("resume");
const resumeUpload = document.getElementById("resumeUpload");
const resumeError = document.getElementById("resumeError");

const githubInput = document.getElementById("github");
const portfolioInput = document.getElementById("portfolio");
const linkedinInput = document.getElementById("linkedin");

const targetRole = document.getElementById("targetRole");

const analyzeButton = document.getElementById("analyzeButton");


/* ==================== CONSTANTS ==================== */

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

const ALLOWED_FILE_TYPES = [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
];


/* ==================== RESUME UPLOAD ==================== */

resumeInput.addEventListener("change", function () {

    const file = resumeInput.files[0];

    // Reset previous error
    resumeError.textContent = "";

    if (!file) {
        return;
    }


    /* Check file type */

    if (!ALLOWED_FILE_TYPES.includes(file.type)) {

        resumeError.textContent =
            "Please upload a PDF, DOC or DOCX file.";

        resumeInput.value = "";

        return;
    }


    /* Check file size */

    if (file.size > MAX_FILE_SIZE) {

        resumeError.textContent =
            "File size must be less than 10 MB.";

        resumeInput.value = "";

        return;
    }


    /* Display selected filename */

    const uploadContent =
        resumeUpload.querySelector(".upload-content");

    uploadContent.innerHTML = `
        <strong>${escapeHTML(file.name)}</strong>
        <span>${formatFileSize(file.size)}</span>
    `;

    resumeUpload.classList.add("file-selected");

});


/* ==================== URL VALIDATION ==================== */

function isValidURL(value) {

    if (!value.trim()) {
        return true;
    }

    try {

        const url = new URL(value);

        return (
            url.protocol === "http:" ||
            url.protocol === "https:"
        );

    } catch {

        return false;

    }
}


/* ==================== GITHUB VALIDATION ==================== */

function validateGithub(value) {

    if (!value.trim()) {
        return true;
    }

    /*
        At the moment the input accepts:

        https://github.com/username

        We keep this validation fairly simple because
        the backend will perform the actual verification.
    */

    try {

        const url = new URL(value);

        return (
            url.hostname === "github.com" ||
            url.hostname === "www.github.com"
        );

    } catch {

        return false;

    }
}


/* ==================== FORM SUBMISSION ==================== */

form.addEventListener("submit", async function (event) {

    event.preventDefault();


    /* Clear previous errors */

    resumeError.textContent = "";


    /* ==================== RESUME ==================== */

    const resume = resumeInput.files[0];

    if (!resume) {

        resumeError.textContent =
            "Please upload your resume.";

        resumeUpload.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });

        return;
    }


    /* ==================== GITHUB ==================== */

    const github = githubInput.value.trim();

    if (!validateGithub(github)) {

        showFieldError(
            githubInput,
            "Please enter a valid GitHub URL."
        );

        return;
    }


    /* ==================== PORTFOLIO ==================== */

    const portfolio = portfolioInput.value.trim();

    if (!isValidURL(portfolio)) {

        showFieldError(
            portfolioInput,
            "Please enter a valid portfolio URL."
        );

        return;
    }


    /* ==================== LINKEDIN ==================== */

    const linkedin = linkedinInput.value.trim();

    if (!isValidURL(linkedin)) {

        showFieldError(
            linkedinInput,
            "Please enter a valid professional profile URL."
        );

        return;
    }


    /* ==================== TARGET ROLE ==================== */

    if (!targetRole.value) {

        showFieldError(
            targetRole,
            "Please select your target role."
        );

        return;
    }


    /* ==================== CREATE FORM DATA ==================== */

    const formData = new FormData();

    formData.append("resume", resume);

    formData.append("github", github);

    formData.append("portfolio", portfolio);

    formData.append("linkedin", linkedin);

    formData.append("targetRole", targetRole.value);


    /* ==================== UI ==================== */

    setLoadingState(true);


    /*
        Backend connection comes next.

        For now, we simulate a successful submission
        and move to the loading page.
    */

    try {

    console.log("Sending profile to CareerLens backend...");

    const analysis = await analyzeProfile(formData);

    console.log("Analysis received:", analysis);

    // Store real analysis temporarily
    sessionStorage.setItem(
        "careerLensAnalysis",
        JSON.stringify(analysis)
    );

    // Go to dashboard
    window.location.href = "dashboard.html";

} catch (error) {

    console.error("Profile submission failed:", error);

    setLoadingState(false);

    alert(error.message || "Something went wrong while analyzing your profile.");
}

});


/* ==================== ERROR DISPLAY ==================== */

function showFieldError(field, message) {

    field.classList.add("input-invalid");

    field.setAttribute(
        "title",
        message
    );

    field.focus();


    /*
        Remove error styling when user starts
        changing the field again.
    */

    field.addEventListener(
        "input",
        function removeError() {

            field.classList.remove("input-invalid");

            field.removeAttribute("title");

            field.removeEventListener(
                "input",
                removeError
            );

        }
    );

}


/* ==================== LOADING STATE ==================== */

function setLoadingState(isLoading) {

    if (isLoading) {

        analyzeButton.disabled = true;

        analyzeButton.innerHTML = `
            <span>Preparing Analysis...</span>
        `;

        analyzeButton.style.opacity = "0.7";

        analyzeButton.style.cursor = "not-allowed";

    } else {

        analyzeButton.disabled = false;

        analyzeButton.innerHTML = `
            <span>Analyze My Profile</span>
            <span class="button-arrow">→</span>
        `;

        analyzeButton.style.opacity = "1";

        analyzeButton.style.cursor = "pointer";

    }

}


/* ==================== FILE SIZE ==================== */

function formatFileSize(bytes) {

    if (bytes < 1024) {
        return `${bytes} B`;
    }

    if (bytes < 1024 * 1024) {
        return `${(bytes / 1024).toFixed(1)} KB`;
    }

    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;

}


/* ==================== HTML ESCAPING ==================== */

function escapeHTML(value) {

    return value
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

}
