// Living Mesh Mission Control — Real-Time Visualizer & Cockpit

let meshData = { nodes: [], recent_events: [], resource_pool: {}, step: 0 };
let selectedNodeId = null;
const canvas = document.getElementById("topologyCanvas");
const ctx = canvas.getContext("2d");

// Resize canvas to container
function resizeCanvas() {
  const container = canvas.parentElement;
  canvas.width = container.clientWidth;
  canvas.height = container.clientHeight;
}
window.addEventListener("resize", resizeCanvas);
resizeCanvas();

// Polling for live mesh state
async function fetchSnapshot() {
  try {
    const res = await fetch("/api/snapshot");
    if (res.ok) {
      meshData = await res.json();
      updateMetrics();
      updateStream();
      updateInspector();
    }
  } catch (err) {
    console.warn("Polling snapshot:", err);
  }
}

setInterval(fetchSnapshot, 800);
fetchSnapshot();

// Update Top Metrics
function updateMetrics() {
  document.getElementById("val-population").innerText = `${meshData.nodes?.length || 0} Nodes`;
  const remaining = meshData.resource_pool?.remaining ?? 10000;
  document.getElementById("val-pool").innerText = `${remaining.toLocaleString()} Tokens`;
  
  const hasAnomaly = meshData.nodes?.some(n => n.recent_anomaly && !n.recent_anomaly.resolved);
  const statusElem = document.getElementById("val-mesh-status");
  if (hasAnomaly) {
    statusElem.innerText = "⚡ ANOMALY DETECTED";
    statusElem.className = "status-badge red";
  } else {
    statusElem.innerText = "● EQUILIBRIUM";
    statusElem.className = "status-badge live";
  }
}

// Update Cognitive Event Stream
function updateStream() {
  const container = document.getElementById("cognitiveTerminal");
  if (!meshData.recent_events) return;
  
  container.innerHTML = "";
  meshData.recent_events.forEach(evt => {
    const div = document.createElement("div");
    let cls = "log-entry";
    if (evt.event_type.includes("anomaly") || evt.event_type.includes("spike") || evt.event_type.includes("attack")) {
      cls += " anomaly";
    } else if (evt.event_type.includes("healing") || evt.event_type.includes("rebalanced") || evt.event_type.includes("index")) {
      cls += " healing";
    } else if (evt.event_type.includes("consensus") || evt.event_type.includes("spawned")) {
      cls += " consensus";
    }
    div.className = cls;
    div.innerHTML = `
      <span class="log-time">[${evt.timestamp || "00:00:00"}]</span>
      <span class="log-tag">${(evt.event_type || "EVENT").toUpperCase()}</span>
      <span class="log-msg">${evt.message}</span>
    `;
    container.appendChild(div);
  });
}

// Update Deep Node Inspector
function updateInspector() {
  if (!meshData.nodes || meshData.nodes.length === 0) return;
  
  let node = meshData.nodes.find(n => n.id === selectedNodeId);
  if (!node) {
    node = meshData.nodes[0];
    selectedNodeId = node.id;
  }
  
  document.getElementById("insp-type").innerText = node.type;
  document.getElementById("insp-name").innerText = node.name;
  document.getElementById("insp-id").innerText = node.id.substring(0, 16) + "...";
  document.getElementById("insp-utility").innerText = (node.utility || 1.0).toFixed(3);
  document.getElementById("insp-budget").innerText = (node.budget_left || 1.0).toFixed(2);
  document.getElementById("insp-memories").innerText = `${node.memories_count || 0} Records`;
  
  document.getElementById("insp-state").innerText = JSON.stringify(node.state, null, 2);
  
  const goalsUl = document.getElementById("insp-goals");
  goalsUl.innerHTML = "";
  if (node.goals && node.goals.length > 0) {
    node.goals.forEach(g => {
      const li = document.createElement("li");
      li.innerText = `🎯 ${g.description} [${g.status}]`;
      goalsUl.appendChild(li);
    });
  } else {
    goalsUl.innerHTML = "<li>None configured</li>";
  }
  
  const anomPre = document.getElementById("insp-anomalies");
  if (node.recent_anomaly) {
    anomPre.innerText = JSON.stringify(node.recent_anomaly, null, 2);
  } else {
    anomPre.innerText = "No recent anomalies. System nominal.";
  }
}

// Interactive Chaos Button Handlers
async function triggerChaos(endpoint) {
  try {
    const btn = event.currentTarget;
    btn.style.transform = "scale(0.96)";
    setTimeout(() => btn.style.transform = "", 150);
    
    await fetch(endpoint, { method: "POST" });
    fetchSnapshot();
  } catch (err) {
    console.error("Chaos trigger error:", err);
  }
}

document.getElementById("btn-chaos-db").onclick = () => triggerChaos("/api/chaos/db");
document.getElementById("btn-chaos-svc").onclick = () => triggerChaos("/api/chaos/service");
document.getElementById("btn-chaos-sec").onclick = () => triggerChaos("/api/chaos/security");
document.getElementById("btn-chaos-mkt").onclick = () => triggerChaos("/api/chaos/market");
document.getElementById("btn-chaos-crash").onclick = () => triggerChaos("/api/chaos/crash");
document.getElementById("btn-chaos-vote").onclick = () => triggerChaos("/api/consensus/trigger");
document.getElementById("btn-chaos-spawn").onclick = () => triggerChaos("/api/spawn/investigator");

// Canvas Topology Interactive Rendering
let nodePositions = [];
let animAngle = 0;

function drawTopology() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  const cx = canvas.width / 2;
  const cy = canvas.height / 2;
  const radius = Math.min(cx, cy) * 0.65;
  const nodes = meshData.nodes || [];
  
  animAngle += 0.005;
  nodePositions = [];

  // Draw central mesh hub ring
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.strokeStyle = "rgba(0, 240, 255, 0.08)";
  ctx.lineWidth = 1.5;
  ctx.setLineDash([4, 6]);
  ctx.stroke();
  ctx.setLineDash([]);

  // Calculate node positions in orbit
  nodes.forEach((node, i) => {
    let nx, ny;
    if (node.type === "LivingCommander") {
      nx = cx;
      ny = cy;
    } else {
      const angle = (i / Math.max(1, nodes.length - 1)) * Math.PI * 2 + animAngle;
      nx = cx + Math.cos(angle) * radius;
      ny = cy + Math.sin(angle) * radius;
    }
    nodePositions.push({ node, x: nx, y: ny });
  });

  // Draw inter-node communication lines & energy pulses
  for (let i = 0; i < nodePositions.length; i++) {
    for (let j = i + 1; j < nodePositions.length; j++) {
      const p1 = nodePositions[i];
      const p2 = nodePositions[j];
      
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.strokeStyle = "rgba(0, 240, 255, 0.04)";
      ctx.lineWidth = 1;
      ctx.stroke();

      // Energy packet pulse
      const t = (Date.now() * 0.001 + i * 0.3) % 1;
      const px = p1.x + (p2.x - p1.x) * t;
      const py = p1.y + (p2.y - p1.y) * t;
      ctx.beginPath();
      ctx.arc(px, py, 1.5, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(0, 240, 255, 0.3)";
      ctx.fill();
    }
  }

  // Draw Nodes
  nodePositions.forEach(np => {
    const node = np.node;
    const isSelected = node.id === selectedNodeId;
    const hasAnomaly = node.recent_anomaly && !node.recent_anomaly.resolved;
    
    // Node Color
    let color = "#00f0ff";
    if (hasAnomaly) color = "#ff3366";
    else if (node.is_dormant) color = "#5c6b84";
    else if (node.type === "LivingCommander") color = "#9d4edd";

    // Glowing Pulse
    const pulseSize = Math.sin(Date.now() * 0.004 + np.x) * 3;
    ctx.beginPath();
    ctx.arc(np.x, np.y, (isSelected ? 20 : 15) + pulseSize, 0, Math.PI * 2);
    ctx.fillStyle = hasAnomaly ? "rgba(255, 51, 102, 0.15)" : "rgba(0, 240, 255, 0.1)";
    ctx.fill();

    // Node Core
    ctx.beginPath();
    ctx.arc(np.x, np.y, isSelected ? 12 : 9, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.shadowColor = color;
    ctx.shadowBlur = isSelected ? 16 : 8;
    ctx.fill();
    ctx.shadowBlur = 0;

    // Node Label
    ctx.font = "10px 'Inter', sans-serif";
    ctx.fillStyle = isSelected ? "#ffffff" : "#8896ab";
    ctx.textAlign = "center";
    ctx.fillText(node.name.replace("_", " "), np.x, np.y + 24);
  });

  requestAnimationFrame(drawTopology);
}

// Canvas Click Selection
canvas.addEventListener("click", e => {
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;

  for (const np of nodePositions) {
    const dist = Math.hypot(np.x - mx, np.y - my);
    if (dist < 25) {
      selectedNodeId = np.node.id;
      updateInspector();
      break;
    }
  }
});

drawTopology();
