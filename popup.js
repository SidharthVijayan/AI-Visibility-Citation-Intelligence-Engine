document.getElementById("analyze").onclick = async () => {
  let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  document.getElementById("dashboard").innerHTML = "Analyzing...";

  try {
    const res = await fetch("https://ai-visibility-citation-intelligence-whm5.onrender.com/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ url: tab.url })
    });

    const data = await res.json();

    document.getElementById("dashboard").innerHTML = `
      
      <div class="card">
        <div class="score-circle" style="--percent:${data.final_score}%">
          <div class="score-inner">${data.final_score}</div>
        </div>
      </div>

      <div class="card">
        <h3>Performance Breakdown</h3>

        <div>SEO Score: ${data.seo_score}</div>
        <div class="bar">
          <div class="bar-fill seo" style="width:${data.seo_score}%"></div>
        </div>

        <div style="margin-top:10px;">GEO Score: ${data.geo_score}</div>
        <div class="bar">
          <div class="bar-fill geo" style="width:${data.geo_score}%"></div>
        </div>
      </div>

      <div class="card">
        <h3>AI Visibility</h3>
        <span class="badge ${data.citation_status === "CITED" ? "good" : "bad"}">
          ${data.citation_status}
        </span>
      </div>

      <div class="card">
        <h3>Issues</h3>
        ${data.issues.map(i => `<div class="issue">${i}</div>`).join("")}
      </div>

      <div class="card">
        <h3>AI Suggestions</h3>
        <div class="ai-box">${data.ai_rewrite}</div>
      </div>

    `;
  } catch (error) {
    document.getElementById("dashboard").innerHTML = "Error loading data";
  }
};
