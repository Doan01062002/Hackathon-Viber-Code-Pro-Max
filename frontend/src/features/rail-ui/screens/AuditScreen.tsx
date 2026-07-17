import { SectionCard } from "@/features/rail-ui/components/Primitives";
import { auditLogs } from "@/features/rail-ui/mockData";

export function AuditScreen() {
  return (
    <div className="page-stack">
      <SectionCard title="Bộ lọc kiểm toán" subtitle="Lọc theo người thao tác, hành động và thời điểm thay đổi.">
        <div className="form-grid">
          <label className="field">
            <span>Người thao tác</span>
            <input className="input" defaultValue="Tất cả" />
          </label>
          <label className="field">
            <span>Hành động</span>
            <input className="input" defaultValue="Tất cả" />
          </label>
          <label className="field">
            <span>Ngày</span>
            <input className="input" defaultValue="17/07/2026" />
          </label>
        </div>
      </SectionCard>

      <SectionCard
        title="Bảng nhật ký kiểm toán"
        subtitle="Theo dõi rõ actor, before, after để truy vết mọi thay đổi quan trọng."
      >
        <div className="table-wrap">
          <table className="data-table audit-table">
            <thead>
              <tr>
                <th>Actor</th>
                <th>Hành động</th>
                <th>Thực thể</th>
                <th>Thời gian</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.map((item) => (
                <tr key={`${item.actor}-${item.time}`}>
                  <th scope="row">{item.actor}</th>
                  <td>{item.action}</td>
                  <td>{item.entity}</td>
                  <td>{item.time}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>

      <div className="two-up">
        <SectionCard title="Dữ liệu trước thay đổi" subtitle="Giá trị hệ thống ghi nhận trước khi cập nhật.">
          <pre className="code-block">{auditLogs[0]?.before}</pre>
        </SectionCard>
        <SectionCard title="Dữ liệu sau thay đổi" subtitle="Giá trị mới để đối chiếu và xác thực quyết định.">
          <pre className="code-block">{auditLogs[0]?.after}</pre>
        </SectionCard>
      </div>
    </div>
  );
}
