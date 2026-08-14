/**
 * Signal Loom v4 design philosophy: a frontier instrument bench for systems
 * that evolve laws, histories, computation, culture, and substrate. Controls
 * stay explicit, research claims stay bounded, and disconnected state is
 * always visible instead of being replaced by fabricated telemetry.
 */
import { useState } from "react";
import type { ReactNode } from "react";
import { Atom, BrainCircuit, Clock3, Code2, Database, GitBranch, Globe2, Layers3, LockKeyhole, Network, Play, Radio, RotateCcw, ScrollText, ShieldCheck, Sparkles, Trophy, WandSparkles } from "lucide-react";

type Tone = "cyan" | "copper" | "chartreuse" | "lavender";
type Props = { generation: number; onEvent?: (text: string, tone?: Tone) => void };
const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

function Result({ value }: { value: unknown }) {
  if (value === null || value === undefined) return null;
  return <pre className="v4-result">{JSON.stringify(value, null, 2)}</pre>;
}

function Heading({ index, kicker, title, icon }: { index: string; kicker: string; title: string; icon: ReactNode }) {
  return <div className="v2-panel-heading"><div className="v2-index">{index}</div><div><div className="section-kicker">{kicker}</div><h3>{title}</h3></div><span className="v2-heading-icon">{icon}</span></div>;
}

function useV4Api(onEvent?: Props["onEvent"]) {
  const [token, setToken] = useState(() => window.sessionStorage.getItem("beast-v4-token") ?? "");
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState("");
  const request = async <T,>(path: string, init: RequestInit = {}) => {
    if (!token) throw new Error("Paste a v4 operator token to connect the frontier plane.");
    const response = await fetch(`${API_BASE}${path}`, { ...init, headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}`, ...(init.headers ?? {}) } });
    if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail ?? `API ${response.status}`);
    setConnected(true);
    return response.json() as Promise<T>;
  };
  const run = async <T,>(action: () => Promise<T>, event?: string, tone: Tone = "cyan") => {
    try { const result = await action(); setError(""); if (event) onEvent?.(event, tone); return result; }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Request failed"); return undefined; }
  };
  const saveToken = (value: string) => { setToken(value); window.sessionStorage.setItem("beast-v4-token", value); setConnected(false); setError(""); };
  return { token, connected, error, request, run, saveToken };
}

function Input({ label, value, onChange, placeholder, type = "text" }: { label: string; value: string; onChange: (value: string) => void; placeholder: string; type?: string }) {
  return <label className="v4-field"><span>{label}</span><input aria-label={label} type={type} value={value} placeholder={placeholder} onChange={(event) => onChange(event.target.value)} /></label>;
}

function ConnectionBar({ api, generation }: { api: ReturnType<typeof useV4Api>; generation: number }) {
  return <div className="v4-connection-bar"><div className="v4-connection-status"><span className={`v4-connection-dot ${api.connected ? "connected" : ""}`} /><strong>{api.connected ? "V4 FRONTIER CONNECTED" : "V4 FRONTIER DISCONNECTED"}</strong><small>G{String(generation).padStart(4, "0")} / bounded research plane</small></div><input aria-label="BEAST v4 operator token" type="password" value={api.token} onChange={(event) => api.saveToken(event.target.value)} placeholder="paste v4 operator JWT" /><code>{API_BASE || "same-origin API"}</code>{api.error && <span className="v4-api-error">{api.error}</span>}</div>;
}

function UniversePanel({ api }: { api: ReturnType<typeof useV4Api> }) {
  const [id, setId] = useState("universe-0"); const [law, setLaw] = useState("entropy_gradient"); const [result, setResult] = useState<unknown>(null);
  const run = async () => { const value = await api.run(() => api.request(`/v4/universes/${encodeURIComponent(id)}/branch`, { method: "POST", body: JSON.stringify({ law }) }), `universe branch / ${id}`, "cyan"); if (value) setResult(value); };
  return <article className="v4-card v4-card-wide"><Heading index="18" kicker="COSMOLOGY / BRANCH CONTROL" title="Split the universe" icon={<Globe2 size={17} />} /><p className="v4-note">Branching is explicit and inspectable: one changed law, one named child universe, one divergence record.</p><div className="v4-form-grid"><Input label="Universe ID" value={id} onChange={setId} placeholder="universe-0" /><label className="v4-field"><span>Law mutation</span><select value={law} onChange={(event) => setLaw(event.target.value)}><option value="entropy_gradient">entropy gradient</option><option value="causality">causality</option><option value="conservation_of_tokens">token conservation</option><option value="information_limit">information limit</option></select></label></div><button className="v4-action cyan-action" onClick={run}><GitBranch size={13} /> Branch universe</button><Result value={result} /></article>;
}

function PhysicsPanel({ api }: { api: ReturnType<typeof useV4Api> }) {
  const [form, setForm] = useState({ universe_id: "universe-0", name: "local_invariant", invariant: "information remains bounded" }); const [result, setResult] = useState<unknown>(null);
  const run = async () => { const value = await api.run(() => api.request("/v4/physics/mutations", { method: "POST", body: JSON.stringify(form) }), "physics mutation / proposed", "copper"); if (value) setResult(value); };
  return <article className="v4-card"><Heading index="19" kicker="PHYSICS / FORMAL INVARIANTS" title="Evolve the laws" icon={<Atom size={17} />} /><div className="v4-form-stack"><Input label="Universe" value={form.universe_id} onChange={(value) => setForm({ ...form, universe_id: value })} placeholder="universe-0" /><Input label="Law name" value={form.name} onChange={(value) => setForm({ ...form, name: value })} placeholder="local_invariant" /><Input label="Invariant statement" value={form.invariant} onChange={(value) => setForm({ ...form, invariant: value })} placeholder="bounded information" /></div><button className="v4-action copper-action" onClick={run}><Sparkles size={13} /> Propose law</button><Result value={result} /></article>;
}

function TemporalPanel({ api }: { api: ReturnType<typeof useV4Api> }) {
  const [form, setForm] = useState({ organism_id: "organism-0", ancestor_id: "ancestor-0", strategy_name: "revised_bridge", revised_strategy: "return 1" }); const [proposal, setProposal] = useState<unknown>(null); const [proposalId, setProposalId] = useState("");
  const propose = async () => { const value = await api.run(() => api.request<{ proposal_id?: string }>("/v4/temporal/proposals", { method: "POST", body: JSON.stringify(form) }), "temporal revision / proposed", "lavender"); if (value) { setProposal(value); setProposalId(value.proposal_id ?? ""); } };
  const apply = async () => { const value = await api.run(() => api.request(`/v4/temporal/apply`, { method: "POST", body: JSON.stringify({ proposal_id: proposalId }) }), "temporal revision / applied", "lavender"); if (value) setProposal(value); };
  return <article className="v4-card"><Heading index="20" kicker="TEMPORAL ENGINE / CAUSAL CONE" title="Revise without paradox" icon={<Clock3 size={17} />} /><div className="v4-form-grid"><Input label="Organism" value={form.organism_id} onChange={(value) => setForm({ ...form, organism_id: value })} placeholder="organism-0" /><Input label="Ancestor" value={form.ancestor_id} onChange={(value) => setForm({ ...form, ancestor_id: value })} placeholder="ancestor-0" /><Input label="Strategy name" value={form.strategy_name} onChange={(value) => setForm({ ...form, strategy_name: value })} placeholder="revised_bridge" /></div><textarea className="v4-code-editor" value={form.revised_strategy} onChange={(event) => setForm({ ...form, revised_strategy: event.target.value })} aria-label="Revised strategy" spellCheck={false} /><div className="v4-action-row"><button className="v4-action lavender-action" onClick={propose}><Clock3 size={13} /> Propose revision</button>{proposalId && <button className="v4-action" onClick={apply}><RotateCcw size={13} /> Apply {proposalId.slice(0, 8)}</button>}</div><Result value={proposal} /></article>;
}

function ComputationPanel({ api }: { api: ReturnType<typeof useV4Api> }) {
  const [tape, setTape] = useState("1011"); const [steps, setSteps] = useState("128"); const [result, setResult] = useState<unknown>(null);
  const run = async () => { const value = await api.run(() => api.request("/v4/computation/run", { method: "POST", body: JSON.stringify({ input_tape: tape, step_limit: Number(steps), transition_table: {} }) }), "universal computation / bounded run", "cyan"); if (value) setResult(value); };
  return <article className="v4-card"><Heading index="21" kicker="UNIVERSAL COMPUTATION / BOUNDED" title="Run the machine" icon={<Code2 size={17} />} /><div className="v4-form-grid"><Input label="Input tape" value={tape} onChange={setTape} placeholder="1011" /><Input label="Step limit" value={steps} onChange={setSteps} placeholder="128" type="number" /></div><button className="v4-action cyan-action" onClick={run}><Play size={13} /> Execute bounded tape</button><Result value={result} /><span className="v4-safety-note"><LockKeyhole size={12} /> isolated execution / explicit step budget</span></article>;
}

function ImmunityPanel({ api }: { api: ReturnType<typeof useV4Api> }) {
  const [form, setForm] = useState({ organism_id: "organism-0", attack_pattern: "prompt_injection", defense_strategy: "reject_unknown", effectiveness: "0.92", generation: "0" }); const [result, setResult] = useState<unknown>(null);
  const run = async () => { const value = await api.run(() => api.request("/v4/immunity/antibodies", { method: "POST", body: JSON.stringify({ ...form, effectiveness: Number(form.effectiveness), generation: Number(form.generation) }) }), "civilization immunity / antibody donated", "chartreuse"); if (value) setResult(value); };
  return <article className="v4-card"><Heading index="22" kicker="CIVILIZATION IMMUNITY / DEFENSE" title="Build collective antibodies" icon={<ShieldCheck size={17} />} /><div className="v4-form-stack"><Input label="Organism" value={form.organism_id} onChange={(value) => setForm({ ...form, organism_id: value })} placeholder="organism-0" /><Input label="Attack pattern" value={form.attack_pattern} onChange={(value) => setForm({ ...form, attack_pattern: value })} placeholder="prompt_injection" /><Input label="Defense strategy" value={form.defense_strategy} onChange={(value) => setForm({ ...form, defense_strategy: value })} placeholder="reject_unknown" /></div><button className="v4-action chartreuse-action" onClick={run}><ShieldCheck size={13} /> Donate antibody</button><Result value={result} /></article>;
}

function EpistemicPanel({ api }: { api: ReturnType<typeof useV4Api> }) {
  const [form, setForm] = useState({ organism_id: "organism-0", observation: "0.72", learning_rate: "0.2" }); const [result, setResult] = useState<unknown>(null);
  const run = async () => { const value = await api.run(() => api.request("/v4/epistemic/update", { method: "POST", body: JSON.stringify({ ...form, observation: Number(form.observation), learning_rate: Number(form.learning_rate) }) }), "epistemic update / uncertainty revised", "lavender"); if (value) setResult(value); };
  return <article className="v4-card"><Heading index="23" kicker="EPISTEMICS / UNCERTAINTY" title="Keep doubt measurable" icon={<BrainCircuit size={17} />} /><div className="v4-form-grid"><Input label="Organism" value={form.organism_id} onChange={(value) => setForm({ ...form, organism_id: value })} placeholder="organism-0" /><Input label="Observation [0,1]" value={form.observation} onChange={(value) => setForm({ ...form, observation: value })} placeholder="0.72" type="number" /><Input label="Learning rate" value={form.learning_rate} onChange={(value) => setForm({ ...form, learning_rate: value })} placeholder="0.2" type="number" /></div><button className="v4-action lavender-action" onClick={run}><BrainCircuit size={13} /> Update belief state</button><Result value={result} /></article>;
}

function MemoryPanel({ api }: { api: ReturnType<typeof useV4Api> }) {
  const [form, setForm] = useState({ name: "bridge_v4", descriptor: "coordination", source_code: "return 1", effectiveness: "0.8", author_id: "organism-0", generation: "0" }); const [result, setResult] = useState<unknown>(null);
  const record = async () => { const value = await api.run(() => api.request("/v4/memory/record", { method: "POST", body: JSON.stringify({ ...form, effectiveness: Number(form.effectiveness), generation: Number(form.generation) }) }), "memory palace / record committed", "copper"); if (value) setResult(value); };
  const snapshot = async () => { const value = await api.run(() => api.request("/v4/memory/snapshot"), "memory palace / snapshot read", "cyan"); if (value) setResult(value); };
  return <article className="v4-card"><Heading index="24" kicker="MEMORY PALACE / CULTURAL GEOMETRY" title="Place what survives" icon={<Database size={17} />} /><div className="v4-form-grid"><Input label="Memory name" value={form.name} onChange={(value) => setForm({ ...form, name: value })} placeholder="bridge_v4" /><Input label="Descriptor" value={form.descriptor} onChange={(value) => setForm({ ...form, descriptor: value })} placeholder="coordination" /><Input label="Author" value={form.author_id} onChange={(value) => setForm({ ...form, author_id: value })} placeholder="organism-0" /></div><textarea className="v4-code-editor" value={form.source_code} onChange={(event) => setForm({ ...form, source_code: event.target.value })} aria-label="Memory source code" spellCheck={false} /><div className="v4-action-row"><button className="v4-action copper-action" onClick={record}><Database size={13} /> Record memory</button><button className="v4-action" onClick={snapshot}><Radio size={13} /> Read palace</button></div><Result value={result} /></article>;
}

function WritingPanel({ api }: { api: ReturnType<typeof useV4Api> }) {
  const [action, setAction] = useState("cooperate"); const [result, setResult] = useState<unknown>(null); const encode = async () => { const value = await api.run(() => api.request("/v4/writing/encode", { method: "POST", body: JSON.stringify({ action, parameters: {}, context: {} }) }), "writing system / token encoded", "chartreuse"); if (value) setResult(value); }; const evolve = async () => { const value = await api.run(() => api.request("/v4/writing/evolve", { method: "POST" }), "writing system / grammar evolved", "chartreuse"); if (value) setResult(value); };
  return <article className="v4-card"><Heading index="25" kicker="WRITING SYSTEM / UNIVERSAL GRAMMAR" title="Let language evolve" icon={<ScrollText size={17} />} /><Input label="Intent token" value={action} onChange={setAction} placeholder="cooperate" /><div className="v4-action-row"><button className="v4-action chartreuse-action" onClick={encode}><WandSparkles size={13} /> Encode intent</button><button className="v4-action" onClick={evolve}><RotateCcw size={13} /> Evolve grammar</button></div><Result value={result} /></article>;
}

function TournamentPanel({ api }: { api: ReturnType<typeof useV4Api> }) {
  const [result, setResult] = useState<unknown>(null); const run = async () => { const value = await api.run(() => api.request("/v4/tournaments/round-robin", { method: "POST", body: JSON.stringify({ generation: 0 }) }), "tournament / round robin complete", "copper"); if (value) setResult(value); };
  return <article className="v4-card"><Heading index="26" kicker="ADVERSARIAL TOURNAMENT / ELO" title="Make strategies earn it" icon={<Trophy size={17} />} /><p className="v4-note">A strategy is only frontier-grade if it survives repeated opponents, not a single friendly fitness trace.</p><button className="v4-action copper-action" onClick={run}><Trophy size={13} /> Run round robin</button><Result value={result} /></article>;
}

function MorphogenesisPanel({ api }: { api: ReturnType<typeof useV4Api> }) {
  const [steps, setSteps] = useState("10"); const [result, setResult] = useState<unknown>(null); const run = async () => { const value = await api.run(() => api.request("/v4/morphogenesis/develop", { method: "POST", body: JSON.stringify({ steps: Number(steps), instructions: [{ type: "divide", condition: "always", parameters: {} }, { type: "connect", condition: "always", parameters: { weight: 0.25 } }] }) }), "morphogenesis / topology developed", "cyan"); if (value) setResult(value); };
  return <article className="v4-card"><Heading index="27" kicker="MORPHOGENETIC AI / NEURAL GROWTH" title="Grow a topology" icon={<Network size={17} />} /><div className="v4-inline-form"><Input label="Development steps" value={steps} onChange={setSteps} placeholder="10" type="number" /><button className="v4-action cyan-action" onClick={run}><Network size={13} /> Develop</button></div><Result value={result} /></article>;
}

function SubstratePanel({ api }: { api: ReturnType<typeof useV4Api> }) {
  const [organism, setOrganism] = useState("organism-0"); const [substrate, setSubstrate] = useState("wasm"); const [result, setResult] = useState<unknown>(null); const run = async () => { const value = await api.run(() => api.request("/v4/substrate/export", { method: "POST", body: JSON.stringify({ organism_id: organism, substrate }) }), `substrate export / ${substrate}`, "lavender"); if (value) setResult(value); };
  return <article className="v4-card"><Heading index="28" kicker="SUBSTRATE EXPORT / PORTABILITY" title="Leave the dashboard" icon={<Layers3 size={17} />} /><div className="v4-form-grid"><Input label="Organism" value={organism} onChange={setOrganism} placeholder="organism-0" /><label className="v4-field"><span>Target substrate</span><select value={substrate} onChange={(event) => setSubstrate(event.target.value)}><option value="wasm">WASM</option><option value="container">container</option><option value="circuit">hardware circuit</option></select></label></div><button className="v4-action lavender-action" onClick={run}><Layers3 size={13} /> Export artifact</button><Result value={result} /></article>;
}

export default function V4Panels({ generation, onEvent }: Props) {
  const api = useV4Api(onEvent);
  return <section className="v4-observatory" id="v4-observatory" aria-label="BEAST v4 frontier panels"><ConnectionBar api={api} generation={generation} /><div className="v4-section-intro"><div><div className="eyebrow"><span className="eyebrow-line" />BEAST v4 / DEVELOPER FRONTIER</div><h2>Build beyond the <em>organism.</em></h2></div><p>Ten instruments expose laws, histories, computation, culture, defense, and portability through an authenticated research plane. Every panel is explicit about its boundary.</p></div><div className="v4-panel-grid"><UniversePanel api={api} /><TemporalPanel api={api} /><ComputationPanel api={api} /><ImmunityPanel api={api} /><EpistemicPanel api={api} /><MemoryPanel api={api} /><WritingPanel api={api} /><TournamentPanel api={api} /><MorphogenesisPanel api={api} /><SubstratePanel api={api} /></div></section>;
}
