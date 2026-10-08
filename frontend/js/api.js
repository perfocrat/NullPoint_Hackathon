/* =========================================================
   CAREERLENS - API HELPERS (shared by input, loading, dashboard)
   ========================================================= */

const JOB_KEY = "careerlens.jobId";

async function parseJSON(response) {
    try {
        return await response.json();
    } catch {
        return null;
    }
}

/* POST the profile form. Resolves with the job id. */
async function startAnalysis(formData) {
    const response = await fetch("/api/analyze", { method: "POST", body: formData });
    const data = await parseJSON(response);

    if (!response.ok || !data || !data.success) {
        throw new Error((data && data.error) || "Could not start the analysis.");
    }

    sessionStorage.setItem(JOB_KEY, data.jobId);
    return data.jobId;
}

function getJobId() {
    return sessionStorage.getItem(JOB_KEY);
}

async function fetchStatus(jobId) {
    const response = await fetch(`/api/status/${encodeURIComponent(jobId)}`);
    const data = await parseJSON(response);

    if (!response.ok || !data || !data.success) {
        throw new Error((data && data.error) || "Lost contact with the analysis.");
    }
    return data;
}

async function fetchResult(jobId) {
    const response = await fetch(`/api/result/${encodeURIComponent(jobId)}`);
    const data = await parseJSON(response);

    if (!response.ok || !data || !data.success) {
        throw new Error((data && data.error) || "Could not load your results.");
    }
    return data.analysis;
}
