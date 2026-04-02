document.getElementById("analyze").onclick = async () => {
  let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  const res = await fetch("http://127.0.0.1:8000/analyze", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ url: tab.url })
  });

  const data = await res.json();

  document.getElementById("output").innerHTML = `
    <h3>SEO Issues</h3>
    <pre>${JSON.stringify(data.issues, null, 2)}</pre>

    <h3>AI Rewrite</h3>
    <pre>${data.ai_rewrite}</pre>

    <h3>GEO Score</h3>
    <p>${data.geo.geo_score} (${data.geo.citation_status})</p>

    <h3>Bot Strategy</h3>
    <pre>${JSON.stringify(data.bot_strategy, null, 2)}</pre>
  `;
};
