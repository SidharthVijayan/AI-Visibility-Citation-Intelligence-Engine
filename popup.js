document.addEventListener("DOMContentLoaded", () => {

  const button = document.getElementById("analyze");

  if (!button) {
    console.error("Button not found");
    return;
  }

  button.addEventListener("click", async () => {
    try {
      const tabs = await chrome.tabs.query({
        active: true,
        currentWindow: true
      });

      if (!tabs || tabs.length === 0) {
        alert("No active tab found.");
        return;
      }

      const currentTab = tabs[0];

      if (!currentTab.url) {
        alert("No URL found.");
        return;
      }

      const dashboardUrl =
        chrome.runtime.getURL("dashboard.html") +
        "?url=" +
        encodeURIComponent(currentTab.url);

      chrome.tabs.create({ url: dashboardUrl });

    } catch (err) {
      console.error("Popup error:", err);
      alert("Something broke. Check console.");
    }
  });

});
