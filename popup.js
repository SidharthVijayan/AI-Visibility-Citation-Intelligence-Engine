document.addEventListener("DOMContentLoaded", () => {
  const button = document.getElementById("analyze");
  const footer = document.querySelector(".footer");

  // --- CONFIGURATION ---
  // 1. Use LOCAL_URL if you are running FastAPI + Ollama on your own computer.
  // 2. Use RENDER_URL once you deploy to the web (Note: Render cannot talk to your local Ollama).
  const LOCAL_URL = "http://127.0.0.1:8000/analyze";
  const RENDER_URL = "https://ai-visibility-citation-intelligence-whm5.onrender.com/analyze";
  
  const ACTIVE_BACKEND = LOCAL_URL; // Change this to RENDER_URL when ready

  if (!button) {
    console.error("Button not found");
    return;
  }

  button.addEventListener("click", async () => {
    try {
      // 1. Get the current active browser tab
      const [tab] = await chrome.tabs.query({
        active: true,
        currentWindow: true
      });

      if (!tab || !tab.url) {
        alert("Please open a valid website first.");
        return;
      }

      button.innerText = "Analyzing... ⏳";
      button.disabled = true;

      // 2. Send the URL to your FastAPI Backend
      const response = await fetch(ACTIVE_BACKEND, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ url: tab.url })
      });

      if (!response.ok) {
        throw new Error(`Server Error: ${response.status}`);
      }

      const data = await response.json();

      // 3. Open the Dashboard with the results
      // We pass the data via URL parameters so the dashboard can display them
      const dashboardUrl = chrome.runtime.getURL("dashboard.html") +
        `?url=${encodeURIComponent(data.url)}` +
        `&seo=${data.seo_score}` +
        `&geo=${data.geo_score}` +
        `&final=${data.final_score || (data.seo_score + data.geo_score) / 2}` +
        `&status=${encodeURIComponent(data.citation_status || "Checking...")}` +
        `&reasoning=${encodeURIComponent(data.reasoning || "Analysis complete.")}`;

      chrome.tabs.create({ url: dashboardUrl });

      // Reset button
      button.innerText = "Open Dashboard";
      button.disabled = false;

    } catch (err) {
      console.error("Popup Error:", err);
      alert("Connection failed! Make sure your FastAPI server is running.");
      button.innerText = "Try Again";
      button.disabled = false;
    }
  });
});
