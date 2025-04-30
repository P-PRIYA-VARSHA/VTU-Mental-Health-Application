document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("survey-form").addEventListener("submit", function (e) {
        e.preventDefault();
        
        let formData = {};
        new FormData(this).forEach((value, key) => { formData[key] = value; });
        
        fetch("/submit_survey", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            alert(`Risk Level: ${data.risk_level}\nRecommendations: ${data.recommendations.join(", ")}`);
        });
    });
});