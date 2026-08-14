/**
 * Signal Loom design philosophy: an observatory control room for cumulative
 * machine culture. Graphite canvas, copper actions, sea-glass signal lines,
 * and editorial typography create a serious production instrument—not a
 * generic admin dashboard. Every interaction should feel like tuning a live
 * system: precise, legible, and quietly responsive.
 */
import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowUpRight,
  Cable,
  ChevronRight,
  CircleStop,
  Database,
  GitBranch,
  Layers3,
  Play,
  Radio,
  RotateCcw,
  Settings2,
  ShieldCheck,
  Sparkles,
  Terminal,
  Zap,
} from "lucide-react";
import V3Panels from "../components/V3Panels";

type Species = "producer" | "consumer" | "decomposer";

const speciesMeta: Record<Species, { label: string; color: string; note: string }> = {
  producer: { label: "Producer", color: "var(--copper)", note: "creates new memes" },
  consumer: { label: "Consumer", color: "var(--cyan)", note: "adopts proven behavior" },
  decomposer: { label: "Decomposer", color: "var(--chartreuse)", note: "recycles dead memes" },
};

const baseChart = [42, 44, 43, 47, 46, 52, 51, 58, 56, 63, 66, 64, 71, 74, 78, 77, 82, 85, 84, 89, 92, 91, 95, 94];

function Sparkline({ data, color = "var(--cyan)", width = 340, height = 82 }: { data: number[]; color?: string; width?: number; height?: number }) {
  const min = Math.min(...data);
  const max = Math.max(...data);
  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * width;
    const y = height - ((value - min) / Math.max(max - min, 1)) * (height - 12) - 6;
    return `${x},${y}`;
  }).join(" ");
  const area = `0,${height} ${points} ${width},${height}`;
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="sparkline" role="img" aria-label="Metric trend">
      <polygon points={area} fill={color} opacity="0.08" />
      <polyline points={points} fill="none" stroke={color} strokeWidth="2" vectorEffect="non-scaling-stroke" />
      <circle cx={width} cy={Number(points.split(" ").at(-1)?.split(",")[1] ?? 0)} r="3.5" fill={color} />
    </svg>
  );
}

function GenerationRuler({ generation, label }: { generation: number; label: string }) {
  return <div className="generation-ruler" aria-label={`${label}, generation ${generation}`}><span className="generation-ruler-label">{label}</span><div className="generation-ruler-track">{Array.from({ length: 14 }, (_, index) => <i key={index} className={index % 4 === 0 ? "major" : ""} />)}</div><span className="generation-ruler-readout">G{String(generation).padStart(4, "0")}</span></div>;
}

function Metric({ label, value, delta, color, data }: { label: string; value: string; delta: string; color: string; data: number[] }) {
  return (
    <div className="metric-block">
      <div className="metric-label"><span className="signal-dot" style={{ background: color }} />{label}</div>
      <div className="metric-value-row"><strong>{value}</strong><span className="metric-delta">{delta}</span></div>
      <Sparkline data={data} color={color} width={150} height={42} />
    </div>
  );
}

export default function Home() {
  const [running, setRunning] = useState(true);
  const [live, setLive] = useState(true);
  const [generation, setGeneration] = useState(842);
  const [speed, setSpeed] = useState(2);
  const [species, setSpecies] = useState<Species>("producer");
  const [apiConnected, setApiConnected] = useState(false);
  const [chart, setChart] = useState(baseChart);
  const [events, setEvents] = useState([
    { time: "14:22:08", kind: "inheritance", text: "consumer-042 adopted bridge_v17", tone: "cyan" },
    { time: "14:21:54", kind: "novelty", text: "new behavior descriptor / lateral-cache", tone: "chartreuse" },
    { time: "14:21:39", kind: "policy", text: "mutation policy tuned by decomposer-019", tone: "copper" },
  ]);

  useEffect(() => {
    if (!running) return;
    const interval = window.setInterval(() => {
      setGeneration((current) => current + 1);
      setChart((current) => [...current.slice(-23), Math.min(99, current.at(-1)! + (Math.random() > 0.35 ? 1 : 0))]);
    }, Math.max(750, 2600 - speed * 550));
    return () => window.clearInterval(interval);
  }, [running, speed]);

  const generationLabel = useMemo(() => String(generation).padStart(4, "0"), [generation]);

  const nudgeEvolution = () => {
    setGeneration((current) => current + 1);
    setEvents((current) => [
      { time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }), kind: "manual", text: `manual step / ${speciesMeta[species].label.toLowerCase()} cohort`, tone: "copper" },
      ...current.slice(0, 2),
    ]);
  };

  const recordV2Event = (text: string, tone = "cyan") => {
    setEvents((current) => [{ time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }), kind: "v2 control", text, tone }, ...current.slice(0, 2)]);
  };

  return (
    <main className="observatory-shell">
      <aside className="observatory-rail">
        <div className="rail-brand"><div className="brand-mark"><img src="/manus-storage/signal-loom-mark_d0943cb1.png" alt="Signal Loom woven loop" /></div><span>LO</span></div>
        <div className="rail-wordmark">SIGNAL<br /><strong>LOOM</strong></div>
        <nav className="rail-nav" aria-label="Observatory navigation">
          <a className="rail-link active" href="#observatory" aria-label="Observatory"><Activity size={17} /><span>OBS</span></a>
          <a className="rail-link" href="#lineage" aria-label="Lineage"><GitBranch size={17} /><span>LIN</span></a>
          <a className="rail-link" href="#memome" aria-label="Memome"><Database size={17} /><span>MEM</span></a>
          <a className="rail-link" href="#runtime" aria-label="Runtime"><Terminal size={17} /><span>RUN</span></a>
        </nav>
        <div className="rail-bottom"><span className="rail-tick" /><span>NODE 01<br />ONLINE</span></div>
      </aside>

      <div className="observatory-body">
        <header className="topbar">
          <div className="context-lockup"><span className="context-path">OBSERVATORY / NODE 01</span><span className="context-divider">/</span><span>LIVE INSTRUMENT</span></div>
          <div className="top-actions"><span className={`status-pill ${apiConnected ? "connected" : ""}`}><span className="status-dot" />{apiConnected ? "API CONNECTED" : "LOCAL SIMULATION"}</span><button className="icon-button" aria-label="Settings"><Settings2 size={17} /></button></div>
        </header>

        <section className="hero-band" id="observatory">
          <div className="hero-copy">
            <div className="eyebrow"><span className="eyebrow-line" />ACTIVE EVOLUTION / EVIDENCE FIRST</div>
            <div className="readout-kicker">CURRENT GENERATION</div>
            <div className="readout-line"><strong>G{generationLabel}</strong><span className="readout-status"><span className="status-dot" />{running ? "ADVANCING" : "PAUSED"}</span></div>
            <h1>Memory is the<br /><em>advantage.</em></h1>
            <p className="hero-lede">A production substrate for agents that accumulate behavior across lifetimes—not just sessions.</p>
            <div className="hero-actions"><button className="primary-button" onClick={() => setRunning((current) => !current)}>{running ? <CircleStop size={16} /> : <Play size={16} />}{running ? "Pause controlled evolution" : "Resume controlled evolution"}</button><button className="text-button" onClick={() => setApiConnected((current) => !current)}><Cable size={15} />{apiConnected ? "Disconnect operator plane" : "Connect operator plane"}<ArrowUpRight size={14} /></button></div>
          </div>
          <div className="hero-pulse"><div className="pulse-kicker"><Radio size={14} /> LIVE EVOLUTION STREAM <span>●</span></div><div className="signal-table"><div><span>POPULATION</span><strong>10,000</strong><small>organisms / stable</small></div><div><span>THROUGHPUT</span><strong>1,000<span className="unit">/s</span></strong><small>batch reproduction</small></div><div><span>ARCHIVE</span><strong>12</strong><small>active shards / healthy</small></div></div><div className="pulse-foot"><span>3 species</span><span className="slash">/</span><span>1.4M memes</span><span className="slash">/</span><span>99.98% health</span></div><div className="orbit-graphic"><span className="orbit orbit-a" /><span className="orbit orbit-b" /><span className="orbit-core" /><span className="orbit-node node-a" /><span className="orbit-node node-b" /><span className="orbit-node node-c" /></div></div>
        </section>

      <section className="metrics-rail" aria-label="Evolution metrics">
        <Metric label="AVERAGE FITNESS" value="0.94" delta="+8.4%" color="var(--cyan)" data={chart.slice(-12)} />
        <Metric label="CULTURAL COMPLEXITY" value="2.81" delta="+22.1%" color="var(--copper)" data={chart.slice(0, 12).map((v) => v * 0.7)} />
        <Metric label="NOVELTY INDEX" value="40" delta="+6 today" color="var(--chartreuse)" data={chart.slice(-12).map((v) => v - 22)} />
        <Metric label="ARCHIVE HEALTH" value="99.98%" delta="STABLE" color="var(--lavender)" data={[98, 98, 99, 99, 99, 99, 99, 100, 99, 100, 100, 99]} />
      </section>

      <section className="control-strip" id="runtime">
        <div className="control-heading"><div className="section-index">01</div><div><div className="section-kicker">CONTROL SURFACE</div><h2>Runtime controls</h2></div></div>
        <div className="control-group"><span className="control-label">EVOLUTION SPEED</span><input aria-label="Evolution speed" type="range" min="1" max="3" value={speed} onChange={(event) => setSpeed(Number(event.target.value))} /><div className="speed-labels"><span>LEISURELY</span><span className={speed === 2 ? "selected" : ""}>NOMINAL</span><span className={speed === 3 ? "selected" : ""}>BURST</span></div></div>
        <div className="species-switcher"><span className="control-label">ACTIVE COHORT</span><div className="species-buttons">{(Object.keys(speciesMeta) as Species[]).map((item) => <button key={item} className={species === item ? "selected" : ""} onClick={() => setSpecies(item)}><span className="signal-dot" style={{ background: speciesMeta[item].color }} />{speciesMeta[item].label}</button>)}</div></div>
        <div className="control-actions"><button className="secondary-button" onClick={nudgeEvolution}><Zap size={15} /> Advance one controlled generation</button><button className={`stream-button ${live ? "live" : ""}`} onClick={() => setLive((current) => !current)}><span className="stream-ring" />{live ? "Observe live stream" : "Resume live stream"}</button></div>
      </section>

      <GenerationRuler generation={generation} label="02 / OBSERVATION WINDOW" />
      <section className="dashboard-grid">
        <article className="panel lineage-panel" id="lineage">
          <div className="panel-header"><div><div className="section-kicker">02 / PERFORMANCE TRACE</div><h2>Fitness across generations</h2></div><div className="panel-meta"><span className="live-chip"><Activity size={13} /> LIVE</span><span>G800 — G{generationLabel}</span></div></div>
          <div className="chart-wrap"><div className="chart-y-labels"><span>1.0</span><span>0.75</span><span>0.50</span><span>0.25</span><span>0.0</span></div><div className="big-chart"><div className="chart-grid-lines"><span /><span /><span /><span /><span /></div><Sparkline data={chart} width={780} height={220} color="var(--cyan)" /><div className="chart-x-labels"><span>G800</span><span>G810</span><span>G820</span><span>G830</span><span>G840</span><span>G{generationLabel}</span></div></div></div>
          <div className="chart-caption"><span><i className="legend-line cyan" /> Mean fitness</span><span><i className="legend-line copper" /> Novelty-adjusted</span><span className="caption-note">Adaptive score / bounded 0—1</span></div>
        </article>

        <article className="panel memome-panel" id="memome">
          <div className="panel-header"><div><div className="section-kicker">03 / CULTURAL ARCHIVE</div><h2>Memome index</h2></div><button className="panel-link">Explore <ChevronRight size={14} /></button></div>
          <div className="memome-image"><img src="/manus-storage/memome-fibers_4f06e3b8.jpg" alt="Abstract woven cultural memory fibers" /><div className="memome-overlay"><span>ACTIVE SHARDS</span><strong>12</strong><small>1.4M records / write healthy</small></div></div>
          <div className="meme-list">
            {[{ name: "bridge_v17", tag: "INHERITED", age: "2m", lift: "+14.8%", color: "cyan" }, { name: "lateral-cache", tag: "NOVEL", age: "6m", lift: "+9.2%", color: "chartreuse" }, { name: "policy-tune_04", tag: "EVOLUTION", age: "11m", lift: "+7.6%", color: "copper" }].map((meme) => <div className="meme-row" key={meme.name}><div className={`meme-marker ${meme.color}`} /><div className="meme-main"><strong>{meme.name}</strong><span>{meme.tag} / {meme.age}</span></div><div className="meme-lift">{meme.lift}<ArrowUpRight size={12} /></div></div>)}
          </div>
        </article>

        <article className="panel species-panel">
          <div className="panel-header"><div><div className="section-kicker">04 / SPECIES COMPOSITION</div><h2>Symbiotic balance</h2></div><GitBranch size={17} className="muted-icon" /></div>
          <div className="species-rings"><div className="ring ring-producer"><span>38%</span><small>PRODUCER</small></div><div className="ring ring-consumer"><span>44%</span><small>CONSUMER</small></div><div className="ring ring-decomposer"><span>18%</span><small>DECOMPOSER</small></div></div>
          <div className="species-footer"><span><i className="legend-dot copper" /> 3,800 creating</span><span><i className="legend-dot cyan" /> 4,400 adopting</span><span><i className="legend-dot chartreuse" /> 1,800 recycling</span></div>
        </article>

        <article className="panel event-panel">
          <div className="panel-header"><div><div className="section-kicker">05 / EVENT STREAM</div><h2>Recent signals</h2></div><Terminal size={17} className="muted-icon" /></div>
          <div className="event-list">{events.map((event, index) => <div className="event-row" key={`${event.time}-${index}`}><span className="event-time">{event.time}</span><span className={`event-dot ${event.tone}`} /><div><strong>{event.kind}</strong><p>{event.text}</p></div></div>)}</div>
          <button className="event-footer">Open event log <ArrowUpRight size={14} /></button>
        </article>
      </section>

      <V3Panels generation={generation} onEvent={recordV2Event} />

        <footer className="footer-bar"><div><span className="footer-mark">LO</span><span>Signal Loom / Control Plane v1.0</span></div><div><span><ShieldCheck size={13} /> guarded runtime</span><span><Database size={13} /> archive synced</span><span><Layers3 size={13} /> {speciesMeta[species].label} selected</span></div><div className="footer-time">UTC 14:22:08</div></footer>
      </div>
    </main>
  );
}
