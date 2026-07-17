import { SectionCard } from "@/features/rail-ui/components/Primitives";
import { scenarioChart, simulationSummary, simulationTable } from "@/features/rail-ui/mockData";

export function SimulationScreen() {
  return (
    <div className="page-stack">
      <SectionCard
        title="Chọn kịch bản mô phỏng"
        subtitle="Chạy thử chính sách trước khi phê duyệt để xem tác động lên doanh thu và lấp đầy."
        actions={<button className="btn btn-primary">Chạy /v1/simulate</button>}
      >
        <div className="scenario-strip">
          <button className="scenario-chip scenario-chip-active" type="button">
            Cuối tuần tháng 7
          </button>
          <button className="scenario-chip" type="button">
            Khung giờ thấp điểm
          </button>
          <button className="scenario-chip" type="button">
            Cân bằng dịp Tết
          </button>
        </div>
      </SectionCard>

      <div className="two-up">
        <SectionCard title="Tóm tắt kết quả" subtitle="Chỉ số chính cần nhìn trước khi bấm phê duyệt.">
          <div className="summary-grid">
            <article>
              <span>Chính sách</span>
              <strong>{simulationSummary.policy}</strong>
            </article>
            <article>
              <span>Tăng doanh thu</span>
              <strong>{simulationSummary.revenueLift}</strong>
            </article>
            <article>
              <span>Tăng lấp đầy</span>
              <strong>{simulationSummary.utilizationLift}</strong>
            </article>
            <article>
              <span>Giảm từ chối chặng ngắn</span>
              <strong>{simulationSummary.rejectedShortTrips}</strong>
            </article>
          </div>
          <p className="section-note">{simulationSummary.note}</p>
        </SectionCard>

        <SectionCard title="Biểu đồ so sánh" subtitle="Doanh thu và sản lượng của từng kịch bản trên cùng thang nhìn.">
          <div className="compare-chart">
            {scenarioChart.map((item) => (
              <div className="compare-col" key={item.name}>
                <span>{item.name}</span>
                <div className="compare-bars">
                  <div className="compare-bar compare-revenue" style={{ height: `${item.revenue}%` }} />
                  <div className="compare-bar compare-volume" style={{ height: `${item.volume}%` }} />
                </div>
              </div>
            ))}
          </div>
        </SectionCard>
      </div>

      <SectionCard title="So sánh AI với hiện tại" subtitle="Bảng ra quyết định gọn, dễ đọc và đủ thuyết phục.">
        <div className="table-wrap">
          <table className="data-table comparison-table">
            <thead>
              <tr>
                <th>Chỉ số</th>
                <th>Hiện tại</th>
                <th>AI đề xuất</th>
              </tr>
            </thead>
            <tbody>
              {simulationTable.map((item) => (
                <tr key={item.metric}>
                  <th scope="row">{item.metric}</th>
                  <td>{item.current}</td>
                  <td>{item.ai}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>

      <SectionCard title="Hành động phê duyệt" subtitle="Giữ thao tác rõ ràng, an toàn và có chủ đích.">
        <div className="action-row">
          <button className="btn btn-primary" type="button">
            Phê duyệt chính sách
          </button>
          <button className="btn btn-ghost" type="button">
            Ghi đè thủ công
          </button>
          <button className="btn btn-ghost" type="button">
            Cập nhật giới hạn
          </button>
        </div>
      </SectionCard>
    </div>
  );
}
