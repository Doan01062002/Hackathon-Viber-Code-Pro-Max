import type { ReactNode } from "react";

type SectionProps = {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
};

export function SectionCard({ title, subtitle, actions, children }: SectionProps) {
  return (
    <section className="surface-card">
      <div className="section-head">
        <div>
          <h3>{title}</h3>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
        {actions ? <div className="section-actions">{actions}</div> : null}
      </div>
      {children}
    </section>
  );
}

export function MetricGrid({
  items,
}: {
  items: Array<{ label: string; value: string; detail?: string; tone: string }>;
}) {
  return (
    <div className="metric-grid">
      {items.map((item) => (
        <article className={`metric-card metric-${item.tone}`} key={item.label}>
          <span>{item.label}</span>
          <strong>{item.value}</strong>
          {item.detail ? <small>{item.detail}</small> : null}
        </article>
      ))}
    </div>
  );
}

export function TinyBars({
  values,
  colorClass = "",
}: {
  values: number[];
  colorClass?: string;
}) {
  return (
    <div className="tiny-bars">
      {values.map((value, index) => (
        <span
          key={`${index}-${value}`}
          className={`tiny-bar ${colorClass}`.trim()}
          style={{ height: `${Math.max(value, 12)}%` }}
        />
      ))}
    </div>
  );
}
