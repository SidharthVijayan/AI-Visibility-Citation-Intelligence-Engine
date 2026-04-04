document.addEventListener("DOMContentLoaded", () => {
  const button = document.getElementById("analyze");
  const LOCAL_URL = "http://127.0.0.1:8080/analyze";

  button.addEventListener("click", async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    button.innerText = "Analyzing... ⏳";
    button.disabled = true;

    try {
      const response = await fetch(LOCAL_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: tab.url })
      });

      if (!response.ok) throw new Error('Server side error');

      const data = await response.json();
      
      // Open the dashboard with the results
      const dashboardUrl = chrome.runtime.getURL("dashboard.html") +
        `?seo=${data.seo_score}&geo=${data.geo_score}&reasoning=${encodeURIComponent(data.reasoning)}`;
      
      chrome.tabs.create({ url: dashboardUrl });
      button.innerText = "Analyze";
      button.disabled = false;

    } catch (err) {
      console.error(err);
      alert("Ensure your terminal is running: python3 -m uvicorn app:app --reload --port 8080");
      button.innerText = "Try Again";
      button.disabled = false;
    }
  });
});
