const params = new URLSearchParams(window.location.search);
const url = params.get("url");

async function loadDashboard() {
  try {
    const res = await fetch("https://ai-visibility-citation-intelligence-whm5.onrender.com/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ url })
    });

    const data = await res.json();

    document.getElementById("content").innerHTML = `
      <div class="card">
        <div class="big-score">${data.final_score}</div>
        <p style="text-align:center;">Overall Score</p>
      </div>

      <div class="card">
        <h3>Performance</h3>
        SEO: ${data.seo_score}
        <div class="bar"><div class="fill seo" style="width:${data.seo_score}%"></div></div>

        GEO: ${data.geo_score}
        <div class="bar"><div class="fill geo" style="width:${data.geo_score}%"></div></div>
      </div>

      <div class="card">
        <h3>AI Visibility</h3>
        <strong>${data.citation_status}</strong>
      </div>

      <div class="card">
        <h3>Why GEO is Low</h3>
        ${data.geo_details.reasons.map(r => `<div class="reason">${r}</div>`).join("")}
      </div>

      <div class="card">
        <h3>How to Fix</h3>
        ${data.geo_details.fixes.map(f => `<div class="fix">${f}</div>`).join("")}
      </div>

      <div class="card">
        <h3>AI Suggestions</h3>
        <p>${data.ai_rewrite}</p>
      </div>
    `;

  } catch (err) {
    document.getElementById("content").innerHTML = "Error loading data.";
    console.error(err);
  }
}

loadDashboard();
