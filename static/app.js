const form = document.querySelector("[data-calculator-form]");
const errorBox = document.querySelector("[data-error]");

if (form) {
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        errorBox.textContent = "";

        const submitButton = form.querySelector("button[type='submit']");
        submitButton.disabled = true;
        submitButton.textContent = "Calculating...";

        const payload = Object.fromEntries(new FormData(form).entries());

        try {
            const response = await fetch("/calculate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || "Unable to calculate dose.");
            }
            window.location.href = data.redirect;
        } catch (error) {
            errorBox.textContent = error.message;
            submitButton.disabled = false;
            submitButton.textContent = "Calculate Dose";
        }
    });
}
