"use client";

import { useState, useEffect } from "react";
import { SectionCard } from "@/features/rail-ui/components/Primitives";
import { apiClient } from "@/lib/api/client";
import { scenarioChart as mockChart, simulationSummary as mockSummary, simulationTable as mockTable } from "@/features/rail-ui/mockData";
import { policyApi } from "@/features/policy/api/policyApi";
import type { PolicyDto } from "@/features/policy/api/policyApi";

interface SimulationCompareData {
  trip_id: number;
  historical_revenue: number;
  simulated_revenue: number;
  revenue_lift_pct: number;
  historical_passenger_km: number;
  simulated_passenger_km: number;
  passenger_km_lift_pct: number;
}

export function SimulationScreen() {
  const [simData, setSimData] = useState<SimulationCompareData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // States cho quản lý Policy Limits
  const [showPolicyPanel, setShowPolicyPanel] = useState(false);
  const [policies, setPolicies] = useState<PolicyDto[]>([]);
  const [fetchingPolicies, setFetchingPolicies] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState<PolicyDto | null>(null);
  const [editFormData, setEditFormData] = useState<{
    name: string;
    min_price: number;
    max_price: number;
    max_step_change: number;
    status: string;
  } | null>(null);
  const [savingPolicy, setSavingPolicy] = useState(false);
  const [policyMessage, setPolicyMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);

  async function loadPolicies() {
    try {
      setFetchingPolicies(true);
      const data = await policyApi.getPolicies();
      setPolicies(data);
    } catch (err) {
      console.error("Lỗi tải chính sách:", err);
    } finally {
      setFetchingPolicies(false);
    }
  }

  useEffect(() => {
    if (showPolicyPanel) {
      loadPolicies();
    }
  }, [showPolicyPanel]);

  // Gọi API so sánh mô phỏng khi component mount hoặc khi bấm chạy
  async function runSimulation(policyId?: number) {
    try {
      setLoading(true);
      setError(null);
      const url = policyId 
        ? `/api/v1/simulation/compare?trip_id=1&policy_id=${policyId}`
        : "/api/v1/simulation/compare?trip_id=1";
      const data = await apiClient.get<SimulationCompareData>(url);
      setSimData(data);
    } catch (err) {
      console.warn("Không kết nối được API mô phỏng, dùng dữ liệu mô phỏng:", err);
      setError("Không thể đồng bộ dữ liệu mô phỏng từ Backend server.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    runSimulation();
  }, []);

  const formatVND = (value: number) => {
    return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(value);
  };

  const formatKM = (value: number) => {
    return new Intl.NumberFormat("vi-VN").format(Math.round(value)) + " Khách-km";
  };

  // Cấu hình chiều cao biểu đồ so sánh dựa trên doanh thu
  const getCompareChartData = () => {
    if (!simData) return mockChart;
    const maxRev = Math.max(simData.historical_revenue, simData.simulated_revenue);
    const maxVol = Math.max(simData.historical_passenger_km, simData.simulated_passenger_km);
    return [
      {
        name: "Lịch sử thực tế",
        revenue: Math.round((simData.historical_revenue / maxRev) * 100),
        volume: Math.round((simData.historical_passenger_km / maxVol) * 100),
      },
      {
        name: "AI đề xuất tối ưu",
        revenue: Math.round((simData.simulated_revenue / maxRev) * 100),
        volume: Math.round((simData.simulated_passenger_km / maxVol) * 100),
      }
    ];
  };

  const chartData = getCompareChartData();

  return (
    <div className="page-stack">
      {error && (
        <div className="banner banner-warning" style={{ backgroundColor: "#3a2a18", borderLeft: "4px solid #d97706", padding: "12px", borderRadius: "6px", color: "#f59e0b", fontSize: "14px", marginBottom: "8px" }}>
          ⚠️ <strong>Cảnh báo:</strong> {error} Hiển thị kịch bản Demo.
        </div>
      )}

      <SectionCard
        title="Chọn kịch bản mô phỏng chính sách"
        subtitle="Chạy giả lập các mức trần/sàn trên dữ liệu hành trình lịch sử để nhìn rõ tác động doanh thu trước khi ban hành."
        actions={
          <button 
            className="btn btn-primary" 
            onClick={() => runSimulation()} 
            disabled={loading}
            style={{ opacity: loading ? 0.7 : 1 }}
          >
            {loading ? "Đang chạy mô phỏng..." : "Kích hoạt Mô Phỏng /v1/simulate"}
          </button>
        }
      >
        <div className="scenario-strip">
          <button className="scenario-chip scenario-chip-active" type="button" onClick={() => runSimulation()}>
            Kịch bản mặc định (Trip #1)
          </button>
          <button className="scenario-chip" type="button" onClick={() => runSimulation(1)}>
            Chính sách Huế - Đà Nẵng
          </button>
          <button className="scenario-chip" type="button" onClick={() => runSimulation()}>
            Cân bằng mùa cao điểm
          </button>
        </div>
      </SectionCard>

      <div className="two-up" style={{ opacity: loading ? 0.6 : 1, transition: "opacity 0.2s" }}>
        <SectionCard title="Tóm tắt kết quả tăng trưởng" subtitle="Các chỉ số tăng trưởng then chốt do AI tính toán.">
          <div className="summary-grid">
            <article>
              <span>Chính sách áp dụng</span>
              <strong>{simData ? `Kịch bản Trip #${simData.trip_id}` : mockSummary.policy}</strong>
            </article>
            <article>
              <span>Tăng doanh thu (Revenue Lift)</span>
              <strong style={{ color: "#10b981" }}>
                {simData ? `+${simData.revenue_lift_pct.toFixed(2)}%` : mockSummary.revenueLift}
              </strong>
            </article>
            <article>
              <span>Tăng sản lượng (Passenger-KM Lift)</span>
              <strong style={{ color: "#10b981" }}>
                {simData ? `+${simData.passenger_km_lift_pct.toFixed(2)}%` : mockSummary.utilizationLift}
              </strong>
            </article>
            <article>
              <span>Trạng thái dự kiến</span>
              <strong>Ổn định hệ số tải</strong>
            </article>
          </div>
          <p className="section-note" style={{ marginTop: "16px", color: "#888" }}>
            {simData 
              ? `Hệ thống mô phỏng đã đối chiếu ${formatVND(simData.historical_revenue)} doanh thu thực tế lịch sử với doanh thu đề xuất từ các Price Quote có hiệu lực.` 
              : mockSummary.note}
          </p>
        </SectionCard>

        <SectionCard title="Biểu đồ so sánh kịch bản (ScenarioCompareChart)" subtitle="Cột xanh ngọc: Doanh thu | Cột xanh dương: Sản lượng Khách-km.">
          <div className="compare-chart" style={{ display: "flex", gap: "24px", justifyContent: "space-around", alignItems: "flex-end", height: "180px", paddingTop: "20px" }}>
            {chartData.map((item) => (
              <div className="compare-col" key={item.name} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "8px" }}>
                <span style={{ fontSize: "11px", color: "#888" }}>{item.name}</span>
                <div className="compare-bars" style={{ display: "flex", gap: "8px", height: "120px", alignItems: "flex-end" }}>
                  <div className="compare-bar compare-revenue" style={{ height: `${item.revenue}%`, width: "20px", backgroundColor: "#10b981", borderRadius: "2px" }} title={`Doanh thu: ${item.revenue}%`} />
                  <div className="compare-bar compare-volume" style={{ height: `${item.volume}%`, width: "20px", backgroundColor: "#3b82f6", borderRadius: "2px" }} title={`Khách-km: ${item.volume}%`} />
                </div>
              </div>
            ))}
          </div>
        </SectionCard>
      </div>

      <SectionCard title="Bảng so sánh chi tiết chỉ số doanh thu & sản lượng" subtitle="Đối chiếu trực quan dữ liệu lịch sử trong cơ sở dữ liệu với giải thuật AI đề xuất.">
        <div className="table-wrap" style={{ opacity: loading ? 0.6 : 1, transition: "opacity 0.2s" }}>
          <table className="data-table comparison-table">
            <thead>
              <tr>
                <th>Chỉ số chặng tàu</th>
                <th>Lịch sử thực tế</th>
                <th>AI đề xuất tối ưu</th>
                <th>Mức tăng trưởng</th>
              </tr>
            </thead>
            <tbody>
              {simData ? (
                <>
                  <tr>
                    <th scope="row">Tổng doanh thu chặng (VND)</th>
                    <td>{formatVND(simData.historical_revenue)}</td>
                    <td style={{ color: "#10b981", fontWeight: "bold" }}>{formatVND(simData.simulated_revenue)}</td>
                    <td style={{ color: "#10b981", fontWeight: "bold" }}>+{simData.revenue_lift_pct.toFixed(2)}%</td>
                  </tr>
                  <tr>
                    <th scope="row">Sản lượng luân chuyển (Khách-km)</th>
                    <td>{formatKM(simData.historical_passenger_km)}</td>
                    <td style={{ color: "#3b82f6", fontWeight: "bold" }}>{formatKM(simData.simulated_passenger_km)}</td>
                    <td style={{ color: "#3b82f6", fontWeight: "bold" }}>+{simData.passenger_km_lift_pct.toFixed(2)}%</td>
                  </tr>
                </>
              ) : (
                mockTable.map((item) => (
                  <tr key={item.metric}>
                    <th scope="row">{item.metric}</th>
                    <td>{item.current}</td>
                    <td>{item.ai}</td>
                    <td>N/A</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </SectionCard>

      <SectionCard title="Hành động phê duyệt chính sách" subtitle="Revenue Manager xem xét phê duyệt kịch bản để áp dụng trực tiếp lên hệ thống đặt vé.">
        <div className="action-row">
          <button className="btn btn-primary" type="button" onClick={() => alert("Đã gửi kịch bản tối ưu hóa lên hệ thống phê duyệt.")}>
            Phê duyệt áp dụng AI
          </button>
          <button className="btn btn-ghost" type="button">
            Ghi đè thủ công
          </button>
          <button className="btn btn-ghost" type="button" onClick={() => setShowPolicyPanel((val) => !val)}>
            {showPolicyPanel ? "Ẩn giới hạn chính sách" : "Cập nhật giới hạn chính sách"}
          </button>
        </div>
      </SectionCard>

      {showPolicyPanel && (
        <SectionCard
          title="Quản lý giới hạn chính sách (Policy Limits)"
          subtitle="Điều chỉnh giá trần, giá sàn và biên độ thay đổi tối đa của từng phân khúc sản phẩm."
          actions={
            <button className="btn btn-ghost" type="button" onClick={() => setShowPolicyPanel(false)}>
              Đóng panel
            </button>
          }
        >
          {policyMessage && (
            <div 
              className={`banner ${policyMessage.type === "success" ? "banner-success" : "banner-warning"}`} 
              style={{
                backgroundColor: policyMessage.type === "success" ? "#143a24" : "#3a2a18",
                borderLeft: `4px solid ${policyMessage.type === "success" ? "#10b981" : "#d97706"}`,
                padding: "12px",
                borderRadius: "6px",
                color: policyMessage.type === "success" ? "#10b981" : "#f59e0b",
                fontSize: "14px",
                marginBottom: "16px"
              }}
            >
              {policyMessage.text}
            </div>
          )}

          {fetchingPolicies ? (
            <p style={{ color: "#888", textAlign: "center", padding: "20px" }}>Đang tải dữ liệu chính sách...</p>
          ) : (
            <div className="table-wrap" style={{ marginBottom: "24px" }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Tên chính sách</th>
                    <th>Giá sàn (Min)</th>
                    <th>Giá trần (Max)</th>
                    <th>Δ Max Step</th>
                    <th>Trạng thái</th>
                    <th>Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {policies.map((p) => (
                    <tr key={p.id}>
                      <td>{p.id}</td>
                      <td><strong>{p.name}</strong></td>
                      <td>{formatVND(p.min_price)}</td>
                      <td>{formatVND(p.max_price)}</td>
                      <td>{formatVND(p.max_step_change)}</td>
                      <td>
                        <span className={`badge badge-${p.status === "active" ? "success" : "neutral"}`} style={{ display: "inline-block", padding: "2px 8px", borderRadius: "4px", backgroundColor: p.status === "active" ? "#143a24" : "#333", color: p.status === "active" ? "#10b981" : "#aaa", fontSize: "11px" }}>
                          {p.status}
                        </span>
                      </td>
                      <td>
                        <button
                          className="btn btn-ghost"
                          type="button"
                          onClick={() => {
                            setSelectedPolicy(p);
                            setEditFormData({
                              name: p.name,
                              min_price: p.min_price,
                              max_price: p.max_price,
                              max_step_change: p.max_step_change,
                              status: p.status,
                            });
                            setPolicyMessage(null);
                          }}
                        >
                          Sửa
                        </button>
                      </td>
                    </tr>
                  ))}
                  {policies.length === 0 && (
                    <tr>
                      <td colSpan={7} style={{ textAlign: "center", color: "#888" }}>
                        Không tìm thấy chính sách nào trong cơ sở dữ liệu.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}

          {editFormData && selectedPolicy && (
            <div 
              style={{
                border: "1px solid #333",
                borderRadius: "8px",
                padding: "20px",
                backgroundColor: "#111"
              }}
            >
              <h3 style={{ fontSize: "16px", fontWeight: "bold", marginBottom: "16px" }}>
                Cập nhật chính sách: {selectedPolicy.name} (ID: {selectedPolicy.id})
              </h3>
              <div 
                className="form-grid" 
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                  gap: "16px",
                  marginBottom: "20px"
                }}
              >
                <label className="field">
                  <span>Tên chính sách</span>
                  <input
                    className="input"
                    value={editFormData.name}
                    onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
                  />
                </label>
                <label className="field">
                  <span>Giá tối thiểu (Sàn)</span>
                  <input
                    className="input"
                    type="number"
                    value={editFormData.min_price}
                    onChange={(e) => setEditFormData({ ...editFormData, min_price: parseFloat(e.target.value) || 0 })}
                  />
                </label>
                <label className="field">
                  <span>Giá tối đa (Trần)</span>
                  <input
                    className="input"
                    type="number"
                    value={editFormData.max_price}
                    onChange={(e) => setEditFormData({ ...editFormData, max_price: parseFloat(e.target.value) || 0 })}
                  />
                </label>
                <label className="field">
                  <span>Biến động bước tối đa</span>
                  <input
                    className="input"
                    type="number"
                    value={editFormData.max_step_change}
                    onChange={(e) => setEditFormData({ ...editFormData, max_step_change: parseFloat(e.target.value) || 0 })}
                  />
                </label>
                <label className="field">
                  <span>Trạng thái</span>
                  <select
                    className="input"
                    value={editFormData.status}
                    onChange={(e) => setEditFormData({ ...editFormData, status: e.target.value })}
                    style={{ backgroundColor: "#222", color: "#fff" }}
                  >
                    <option value="draft">draft</option>
                    <option value="active">active</option>
                    <option value="inactive">inactive</option>
                  </select>
                </label>
              </div>

              <div className="action-row">
                <button
                  className="btn btn-primary"
                  type="button"
                  disabled={savingPolicy}
                  onClick={async () => {
                    if (!editFormData.name || !editFormData.name.trim()) {
                      setPolicyMessage({ text: "Tên chính sách không được để trống.", type: "error" });
                      return;
                    }
                    if (editFormData.min_price > editFormData.max_price) {
                      setPolicyMessage({ text: "Giá sàn (min_price) không được lớn hơn giá trần (max_price).", type: "error" });
                      return;
                    }
                    try {
                      setSavingPolicy(true);
                      await policyApi.updatePolicy(selectedPolicy.id, editFormData);
                      setPolicyMessage({ text: "Cập nhật giới hạn chính sách thành công!", type: "success" });
                      setSelectedPolicy(null);
                      setEditFormData(null);
                      loadPolicies();
                    } catch (err: any) {
                      setPolicyMessage({
                        text: err instanceof Error ? err.message : "Cập nhật thất bại.",
                        type: "error",
                      });
                    } finally {
                      setSavingPolicy(false);
                    }
                  }}
                >
                  {savingPolicy ? "Đang lưu..." : "Lưu thay đổi"}
                </button>
                <button
                  className="btn btn-ghost"
                  type="button"
                  onClick={() => {
                    setSelectedPolicy(null);
                    setEditFormData(null);
                    setPolicyMessage(null);
                  }}
                >
                  Hủy bỏ
                </button>
              </div>
            </div>
          )}
        </SectionCard>
      )}
    </div>
  );
}
