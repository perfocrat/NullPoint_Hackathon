async function analyzeProfile(formData) {
    const response = await fetch("/api/analyze", {
        method: "POST",
        body: formData
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
        throw new Error(data.error || "Analysis failed.");
    }

    return data.analysis;
}