document.addEventListener("DOMContentLoaded", () => {
  const button = document.getElementById("analyze");
  
  // Pointing to your MacBook's Localhost on Port 8080
  const LOCAL_URL = "http://127.0.0.1:8080/analyze";

  button.addEventListener("click", async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    button.innerText = "Analyzing... ⏳";
    button.disabled = true;

    try {
      console.log("Connecting to local engine at 8080...");
      const response = await fetch(LOCAL_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: tab.url })
      });

      if (!response.ok) throw new Error('Engine Error (Check Terminal)');

      const data = await response.json();
      
      // Pass the results to the dashboard
      const dashboardUrl = chrome.runtime.getURL("dashboard.html") +
        `?seo=${data.seo_score}&geo=${data.geo_score}&reasoning=${encodeURIComponent(data.reasoning)}`;
      
      chrome.tabs.create({ url: dashboardUrl });
      
      button.innerText = "Analyze";
      button.disabled = false;

    } catch (err) {
      console.error("Extension Error:", err);
      alert("Analysis Failed. Ensure your Terminal says 'Application startup complete' on Port 8080.");
      button.innerText = "Try Again";
      button.disabled = false;
    }
  });
});
