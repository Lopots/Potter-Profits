import { PotterState } from "@/lib/types";

export function PotterPanel({ potter }: { potter: PotterState }) {
  return (
    <div className="panel potter-panel">
      <div className="potter-head">
        <div>
          <span className="eyebrow">Potter Agent</span>
          <h2>Transparent AI execution</h2>
        </div>
        <span className="status-badge">{potter.mode === "paper" ? "Paper Trading" : "Live Disabled"}</span>
      </div>

      <p className="lead">{potter.mission}</p>

      <div className="insight-box">
        <span className="eyebrow">Current Thinking</span>
        <p>{potter.reasoning_summary}</p>
        <strong>{potter.next_action}</strong>
      </div>

      <div className="guardrails">
        {potter.guardrails.map((guardrail) => (
          <div key={guardrail.name} className="guardrail">
            <span className={`guardrail-dot ${guardrail.status}`} />
            <div>
              <strong>{guardrail.name}</strong>
              <p>{guardrail.detail}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="thought-feed">
        <span className="eyebrow">Thought Stream</span>
        {potter.thoughts.map((thought) => (
          <div key={`${thought.timestamp}-${thought.title}`} className={`thought ${thought.tone}`}>
            <div className="thought-meta">
              <strong>{thought.title}</strong>
              <span>{thought.timestamp}</span>
            </div>
            <p>{thought.detail}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
