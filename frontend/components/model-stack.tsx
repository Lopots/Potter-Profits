import { ModelLayer } from "@/lib/types";

export function ModelStack({ layers }: { layers: ModelLayer[] }) {
  return (
    <div className="panel">
      <div className="section-header">
        <div>
          <span className="eyebrow">Model Stack</span>
          <h2>How Potter decides</h2>
        </div>
        <p>Math leads, ML validates, and AI adds context. The pricing engine stays in control.</p>
      </div>
      <div className="layer-grid">
        {layers.map((layer, index) => (
          <article key={layer.name} className="layer-card">
            <span className="layer-index">0{index + 1}</span>
            <strong>{layer.name}</strong>
            <div className="layer-meta">
              <span>{layer.role}</span>
              <span>{layer.weight}</span>
            </div>
            <p>{layer.purpose}</p>
            <div className="example-row">
              {layer.examples.map((example) => (
                <span key={example} className="mini-pill">
                  {example}
                </span>
              ))}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
