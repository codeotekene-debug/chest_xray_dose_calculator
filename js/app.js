document.addEventListener("DOMContentLoaded", () => {
    const header = document.querySelector(".site-header");

    const updateHeaderShadow = () => {
        if (!header) return;
        header.style.boxShadow = window.scrollY > 40
            ? "0 12px 28px rgba(0, 0, 0, 0.24)"
            : "none";
    };

    updateHeaderShadow();
    window.addEventListener("scroll", updateHeaderShadow);

    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener("click", (event) => {
            const href = anchor.getAttribute("href");

            if (!href || href === "#") return;

            const target = document.querySelector(href);
            if (!target) return;

            event.preventDefault();
            target.scrollIntoView({ behavior: "smooth", block: "start" });
        });
    });

    const revealItems = document.querySelectorAll(".feature-card, .why-card, .process-panel, .cta-band");

    if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                entry.target.classList.add("is-visible");
                observer.unobserve(entry.target);
            });
        }, { threshold: 0.14 });

        revealItems.forEach((item) => observer.observe(item));
    } else {
        revealItems.forEach((item) => item.classList.add("is-visible"));
    }

    document.querySelectorAll(".btn").forEach((button) => {
        button.addEventListener("pointerdown", () => {
            button.style.transform = "scale(0.98)";
        });

        button.addEventListener("pointerup", () => {
            button.style.transform = "";
        });

        button.addEventListener("pointerleave", () => {
            button.style.transform = "";
        });
    });

    const scrollButton = document.createElement("button");
    scrollButton.id = "scrollTop";
    scrollButton.type = "button";
    scrollButton.setAttribute("aria-label", "Scroll to top");
    scrollButton.textContent = "^";
    document.body.appendChild(scrollButton);

    window.addEventListener("scroll", () => {
        scrollButton.style.display = window.scrollY > 420 ? "flex" : "none";
    });

    scrollButton.addEventListener("click", () => {
        window.scrollTo({ top: 0, behavior: "smooth" });
    });
});
