document.getElementById("analyze").onclick = async () => {
  let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  const res = await fetch("http://127.0.0.1:8000/analyze", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ url: tab.url })
  });

  const data = await res.json();

  document.getElementById("dashboard").innerHTML = `
    <div class="card">
      <h3>Overall Score</h3>
      <div class="score">${data.final_score}</div>
    </div>

    <div class="card">
      <h3>SEO Score</h3>
      <div>${data.seo_score}</div>
    </div>

    <div class="card">
      <h3>GEO Score</h3>
      <div>${data.geo_score}</div>
    </div>

    <div class="card">
      <h3>AI Citation</h3>
      <div>${data.citation_status}</div>
    </div>

    <div class="card">
      <h3>Issues</h3>
      <ul>${data.issues.map(i => `<li>${i}</li>`).join("")}</ul>
    </div>

    <div class="card">
      <h3>AI Suggestions</h3>
      <pre>${data.ai_rewrite}</pre>
    </div>
  `;
};
