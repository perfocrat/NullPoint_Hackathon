
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
    const uploadContent = resumeUpload.querySelector(".upload-content");

    resumeError.textContent = "";
    resumeInput.removeAttribute("aria-invalid");
    resumeUpload.classList.toggle("file-selected", Boolean(file));

    if (!file) {
        resetResumeUpload(uploadContent);
        return;
    }


    /* Check file type */

    const validType = ALLOWED_FILE_TYPES.includes(file.type) ||
        /\.(pdf|doc|docx)$/i.test(file.name);
    if (!validType) {

        resumeError.textContent =
            "Please upload a PDF, DOC or DOCX file.";

        resumeInput.value = "";
        resetResumeUpload(uploadContent);
        resumeUpload.classList.remove("file-selected");
        resumeInput.setAttribute("aria-invalid", "true");

        return;
    }


    /* Check file size */

    if (file.size > MAX_FILE_SIZE) {

        resumeError.textContent =
            "File size must be less than 10 MB.";

        resumeInput.value = "";
        resetResumeUpload(uploadContent);
        resumeUpload.classList.remove("file-selected");
        resumeInput.setAttribute("aria-invalid", "true");

        return;
    }


    /* Display selected filename */

    uploadContent.replaceChildren();
    const fileName = document.createElement("strong");
    const fileSize = document.createElement("span");
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    uploadContent.append(fileName, fileSize);

});

function resetResumeUpload(uploadContent) {
    uploadContent.innerHTML = `
        <strong>Upload your resume</strong>
        <span>PDF, DOC or DOCX · Max 10 MB</span>
    `;
}

resumeUpload.addEventListener("dragover", event => {
    event.preventDefault();
    resumeUpload.classList.add("dragging");
});

resumeUpload.addEventListener("dragleave", () => {
    resumeUpload.classList.remove("dragging");
});

resumeUpload.addEventListener("drop", event => {
    event.preventDefault();
    resumeUpload.classList.remove("dragging");
    const [file] = event.dataTransfer.files;
    if (!file) return;
    const transfer = new DataTransfer();
    transfer.items.add(file);
    resumeInput.files = transfer.files;
    resumeInput.dispatchEvent(new Event("change", { bubbles: true }));
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


    setLoadingState(true);
    showFormMessage("");

    try {
        const response = await fetch("/api/analyze", {
            method: "POST",
            body: formData
        });
        const result = await response.json();

        if (!response.ok || !result.success || !result.analysis) {
            throw new Error(result.error || "We couldn't analyze this profile. Please try again.");
        }

        sessionStorage.setItem("careerLensAnalysis", JSON.stringify(result.analysis));
        window.location.href = "loading.html";
    } catch (error) {
        setLoadingState(false);
        showFormMessage(error.message || "Unable to reach CareerLens. Check your connection and try again.");
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
        analyzeButton.setAttribute("aria-busy", "true");

        analyzeButton.innerHTML = `
            <span>Preparing Analysis...</span>
        `;

    } else {

        analyzeButton.disabled = false;
        analyzeButton.removeAttribute("aria-busy");

        analyzeButton.innerHTML = `
            <span>Analyze My Profile</span>
            <span class="button-arrow">→</span>
        `;

    }

}

function showFormMessage(message) {
    let messageNode = document.getElementById("formMessage");
    if (!messageNode) {
        messageNode = document.createElement("p");
        messageNode.id = "formMessage";
        messageNode.className = "form-message";
        messageNode.setAttribute("role", "alert");
        form.querySelector(".submit-section").prepend(messageNode);
    }
    messageNode.textContent = message;
    messageNode.hidden = !message;
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
