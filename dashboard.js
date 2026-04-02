const params = new URLSearchParams(window.location.search);
const url = params.get("url");

async function load() {
  const res = await fetch("https://ai-visibility-citation-intelligence-whm5.onrender.com/analyze", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ url })
  });

  const data = await res.json();

  document.getElementById("content").innerHTML = `
    <div class="card">
      <div class="big-score">${data.final_score}</div>
      <p>Overall Score</p>
    </div>

    <div class="card">
      SEO: ${data.seo_score}<br>
      GEO: ${data.geo_score}
    </div>

    <div class="card">
      Citation: ${data.citation_status}
    </div>

    <div class="card">
      ${data.geo_details.reasons.join("<br>")}
    </div>
  `;
}

load();
