document.addEventListener("DOMContentLoaded", () => {
  const button = document.getElementById("analyze");
  
  // We use Port 8080 to avoid the "Address already in use" error on Macs
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

      const data = await response.json();
      
      // Redirect to your dashboard with the results
      const dashboardUrl = chrome.runtime.getURL("dashboard.html") +
        `?seo=${data.seo_score}&geo=${data.geo_score}&reasoning=${encodeURIComponent(data.reasoning)}`;
      
      chrome.tabs.create({ url: dashboardUrl });
      button.innerText = "Analyze";
      button.disabled = false;

    } catch (err) {
      alert("Connection failed! Run 'python3 -m uvicorn app:app --reload --port 8080' in terminal.");
      button.innerText = "Try Again";
      button.disabled = false;
    }
  });
});
