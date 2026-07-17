import { SectionCard } from "@/features/rail-ui/components/Primitives";
import { alerts } from "@/features/rail-ui/mockData";

function severityClass(value: string) {
  return value === "Trung bình" ? "severity-trung-binh" : "severity-cao";
}

export function AlertsScreen() {
  return (
    <div className="page-stack">
      <SectionCard
        title="Bộ lọc cảnh báo"
        subtitle="Lọc theo mức độ, loại vấn đề và nhóm chặng để xử lý theo ưu tiên."
      >
        <div className="scenario-strip">
          <button className="scenario-chip scenario-chip-active" type="button">
            Tất cả
          </button>
          <button className="scenario-chip" type="button">
            Sắp cháy vé
          </button>
          <button className="scenario-chip" type="button">
            Trống cao
          </button>
          <button className="scenario-chip" type="button">
            Quota cần xem lại
          </button>
        </div>
      </SectionCard>

      <SectionCard
        title="Danh sách cảnh báo"
        subtitle="Tập trung vào cảnh báo đáng xử lý ngay trong ca trực hiện tại."
      >
        <div className="stack-list">
          {alerts.map((alert) => (
            <article className={`alert-card ${severityClass(alert.severity)}`} key={alert.title}>
              <div>
                <span className="alert-pill">{alert.severity}</span>
                <strong>{alert.title}</strong>
                <p>{alert.detail}</p>
              </div>
              <button className="btn btn-ghost" type="button">
                Xem chi tiết
              </button>
            </article>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}
