document.addEventListener("DOMContentLoaded", () => {
  const button = document.getElementById("analyze");
  
  // FIXED: Pointing to your local Mac server on Port 8080
  const LOCAL_URL = "http://127.0.0.1:8080/analyze";

  button.addEventListener("click", async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    button.innerText = "Analyzing... ⏳";
    button.disabled = true;

    try {
      console.log("Connecting to local engine...");
      const response = await fetch(LOCAL_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: tab.url })
      });

      if (!response.ok) throw new Error('Engine Error (500)');

      const data = await response.json();
      
      // Open the dashboard with AI results
      const dashboardUrl = chrome.runtime.getURL("dashboard.html") +
        `?seo=${data.seo_score}&geo=${data.geo_score}&reasoning=${encodeURIComponent(data.reasoning)}`;
      
      chrome.tabs.create({ url: dashboardUrl });
      button.innerText = "Analyze";
      button.disabled = false;

    } catch (err) {
      console.error("Extension Error:", err);
      alert("Make sure the Terminal is running and says 'Application startup complete'.");
      button.innerText = "Try Again";
      button.disabled = false;
    }
  });
});
