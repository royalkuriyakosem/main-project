document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("urlForm");
    const urlInput = document.getElementById("url");
    const resultsDiv = document.getElementById("results");

    if (!form || !urlInput || !resultsDiv) {
        console.error("❌ Required HTML elements missing");
        return;
    }

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const url = urlInput.value.trim();
        if (!url) {
            alert("Please enter a URL");
            return;
        }

        const submitBtn = form.querySelector("button[type='submit']");
        submitBtn.textContent = "Analyzing...";
        submitBtn.disabled = true;

        try {
            const response = await fetch("/predict", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url })   // ✅ ONLY URL
            });

            if (!response.ok) {
                throw new Error(await response.text());
            }

            const data = await response.json();
            renderResults(data);

        } catch (err) {
            console.error("❌ Prediction error:", err);
            alert("Prediction failed. Check backend logs.");
        } finally {
            submitBtn.textContent = "Analyze";
            submitBtn.disabled = false;
        }
    });

});

/* ---------------- RESULT RENDERING ---------------- */

function renderResults(data) {
    document.getElementById("results").style.display = "block";

    // Detected brand
    document.getElementById("detectedBrand").textContent =
        data.brand ? data.brand.toUpperCase() : "N/A";

    // URL Score (invert → legitimacy)
    const urlLegit = 1 - data.url_score;
    setBar("urlScore", urlLegit, "urlValue", "Higher = Legit");

    // DOM Score
    setBar("domScore", data.dom_score, "domValue", "Higher = Similar");

    // Visual Score
    setBar("visualScore", data.visual_score, "visualValue", "Higher = Similar");

    // Fusion Score (invert phishing → legit)
    const legitFusion = 1 - data.hybrid_score;
    setBar("hybridScore", legitFusion, "hybridValue", "Higher = Legit");

    // Final label
    const labelEl = document.getElementById("finalLabel");
    labelEl.textContent = data.final_label.toUpperCase();
    labelEl.className = data.final_label.toLowerCase();
}

function setBar(barId, value, textId, hint) {
    const bar = document.getElementById(barId);
    const text = document.getElementById(textId);

    const percent = Math.max(0, Math.min(1, value)) * 100;
    bar.style.width = `${percent}%`;
    text.textContent = `Score: ${value.toFixed(3)} (${hint})`;
}
