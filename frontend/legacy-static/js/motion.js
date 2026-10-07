/* Lightweight motion and scroll cues shared by every CareerLens page. */
(() => {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const progress = document.createElement("div");
    progress.className = "reading-progress";
    progress.setAttribute("aria-hidden", "true");
    document.body.prepend(progress);

    let scrollQueued = false;
    const updateProgress = () => {
        const scrollable = document.documentElement.scrollHeight - window.innerHeight;
        const amount = scrollable > 0 ? (window.scrollY / scrollable) * 100 : 0;
        progress.style.setProperty("--reading-progress", `${Math.min(100, amount)}%`);
        scrollQueued = false;
    };
    window.addEventListener("scroll", () => {
        if (scrollQueued) return;
        scrollQueued = true;
        window.requestAnimationFrame(updateProgress);
    }, { passive: true });
    window.addEventListener("resize", updateProgress, { passive: true });
    updateProgress();

    if (reduceMotion || !("IntersectionObserver" in window)) return;

    const revealTargets = document.querySelectorAll(
        ".feature-card, .step, .form-section, .score-card, .breakdown-card, .dashboard-section, .evidence-section, .roadmap-item, .cta-content, .loading-container"
    );
    if (!revealTargets.length) return;

    document.documentElement.classList.add("motion-ready");
    const observer = new IntersectionObserver((entries, currentObserver) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            entry.target.classList.add("motion-visible");
            currentObserver.unobserve(entry.target);
        });
    }, { threshold: 0.12, rootMargin: "0px 0px -36px 0px" });

    revealTargets.forEach((element, index) => {
        element.classList.add("motion-reveal");
        element.style.setProperty("--motion-order", `${index % 4}`);
        observer.observe(element);
    });
})();
