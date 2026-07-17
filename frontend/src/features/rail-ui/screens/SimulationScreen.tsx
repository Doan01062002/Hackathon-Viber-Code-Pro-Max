"use client";

import React, { useState, useEffect } from "react";
import { apiClient } from "@/lib/api/client";
import {
  scenarioChart as mockChart,
  simulationSummary as mockSummary,
  simulationTable as mockTable,
} from "@/features/rail-ui/mockData";

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
  const [activeScenario, setActiveScenario] = useState<number | null>(null);

  // Gọi API so sánh mô phỏng khi component mount hoặc khi bấm chạy
  async function runSimulation(policyId?: number) {
    try {
      setLoading(true);
      setError(null);
      setActiveScenario(policyId ?? null);
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
    <div className="space-y-6">

      {error && (
        <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded-lg text-yellow-700 text-xs font-semibold">
          ⚠️ Cảnh báo: {error} Hiển thị kịch bản Demo.
        </div>
      )}

      {/* Scenario Selector Panel */}
      <div className="bg-white border border-outline-variant p-5 rounded-xl shadow-sm space-y-4">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="font-bold text-sm text-on-surface">Chọn kịch bản mô phỏng chính sách</h3>
            <p className="text-xs text-on-surface-variant font-medium">Chạy giả lập các mức trần/sàn trên dữ liệu hành trình lịch sử để nhìn rõ tác động.</p>
          </div>
          <button
            onClick={() => runSimulation(activeScenario ?? undefined)}
            disabled={loading}
            className="px-4 py-2 bg-primary text-on-primary font-bold rounded-lg text-xs hover:brightness-110 active:scale-95 transition-all disabled:opacity-50 cursor-pointer"
          >
            {loading ? "Đang giả lập..." : "Kích hoạt Giả Lập (/v1/simulate)"}
          </button>
        </div>

        <div className="flex gap-2 pt-1 border-t border-outline-variant/35 pt-3">
          <button
            onClick={() => runSimulation()}
            className={`px-4 py-2 rounded-lg font-bold text-xs transition-all ${
              activeScenario === null
                ? "bg-primary text-on-primary"
                : "bg-white border border-outline-variant text-on-surface hover:bg-slate-50"
            }`}
          >
            Kịch bản mặc định (Trip #1)
          </button>
          <button
            onClick={() => runSimulation(1)}
            className={`px-4 py-2 rounded-lg font-bold text-xs transition-all ${
              activeScenario === 1
                ? "bg-primary text-on-primary"
                : "bg-white border border-outline-variant text-on-surface hover:bg-slate-50"
            }`}
          >
            Chính sách Huế - Đà Nẵng
          </button>
          <button
            onClick={() => runSimulation()}
            className="px-4 py-2 rounded-lg font-bold text-xs bg-white border border-outline-variant text-on-surface hover:bg-slate-50 transition-all"
          >
            Cân bằng mùa cao điểm
          </button>
        </div>
      </div>

      {/* Main Simulation Panel: 2 Columns */}
      <div className={`grid grid-cols-1 lg:grid-cols-2 gap-6 transition-opacity duration-200 ${loading ? "opacity-60" : "opacity-100"}`}>
        {/* Left Card: Growth Metrics */}
        <div className="bg-white border border-outline-variant rounded-xl p-5 shadow-sm space-y-4">
          <h3 className="font-bold text-xs text-on-surface uppercase tracking-wider border-b border-outline-variant/30 pb-2">
            Tóm tắt kết quả tăng trưởng
          </h3>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-slate-50 p-3 rounded-lg border border-outline-variant/30 text-xs">
              <span className="text-[9px] text-on-surface-variant font-bold uppercase">Chính sách áp dụng</span>
              <p className="font-bold mt-1 text-on-surface">
                {simData ? `Kịch bản Trip #${simData.trip_id}` : mockSummary.policy}
              </p>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-outline-variant/30 text-xs">
              <span className="text-[9px] text-on-surface-variant font-bold uppercase">Tăng doanh thu (Revenue Lift)</span>
              <p className="font-black mt-1 text-green-600 text-sm">
                {simData ? `+${simData.revenue_lift_pct.toFixed(2)}%` : mockSummary.revenueLift}
              </p>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-outline-variant/30 text-xs">
              <span className="text-[9px] text-on-surface-variant font-bold uppercase">Tăng sản lượng (Pax-KM Lift)</span>
              <p className="font-black mt-1 text-blue-600 text-sm">
                {simData ? `+${simData.passenger_km_lift_pct.toFixed(2)}%` : mockSummary.utilizationLift}
              </p>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-outline-variant/30 text-xs">
              <span className="text-[9px] text-on-surface-variant font-bold uppercase">Trạng thái dự kiến</span>
              <p className="font-bold mt-1 text-on-surface">Ổn định hệ số tải</p>
            </div>
          </div>

          <p className="text-[10px] text-on-surface-variant font-medium leading-relaxed italic bg-slate-50 p-3 rounded border border-dashed border-outline-variant">
            {simData 
              ? `Hệ thống mô phỏng đã đối chiếu ${formatVND(simData.historical_revenue)} doanh thu thực tế lịch sử với doanh thu đề xuất từ các Price Quote có hiệu lực.` 
              : mockSummary.note}
          </p>
        </div>

        {/* Right Card: Comparative Bar Chart */}
        <div className="bg-white border border-outline-variant rounded-xl p-5 shadow-sm flex flex-col justify-between">
          <h3 className="font-bold text-xs text-on-surface uppercase tracking-wider border-b border-outline-variant/30 pb-2 mb-4">
            Biểu đồ so sánh kịch bản (ScenarioCompareChart)
          </h3>

          <div className="flex justify-around items-end h-32 px-4 pb-2 border-b border-outline-variant/35">
            {chartData.map((item) => (
              <div className="flex flex-col items-center gap-3 w-1/2" key={item.name}>
                <div className="flex gap-3 items-end h-24">
                  {/* Revenue Bar */}
                  <div
                    style={{ height: `${item.revenue}%` }}
                    className="w-5 bg-green-500 rounded-t hover:brightness-95 transition-all cursor-help"
                    title={`Doanh thu: ${item.revenue}%`}
                  />
                  {/* Volume Bar */}
                  <div
                    style={{ height: `${item.volume}%` }}
                    className="w-5 bg-blue-500 rounded-t hover:brightness-95 transition-all cursor-help"
                    title={`Khách-km: ${item.volume}%`}
                  />
                </div>
                <span className="text-[10px] font-bold text-on-surface-variant">{item.name}</span>
              </div>
            ))}
          </div>

          <div className="flex justify-center gap-4 text-[9px] font-bold uppercase tracking-wider mt-4">
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 bg-green-500 rounded-sm" />
              <span>Doanh thu</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 bg-blue-500 rounded-sm" />
              <span>Sản lượng khách-km</span>
            </div>
          </div>
        </div>
      </div>

      {/* Detail Comparative Table */}
      <div className="bg-white border border-outline-variant rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-outline-variant bg-white">
          <h3 className="font-bold text-sm text-on-surface">Bảng so sánh chi tiết chỉ số</h3>
          <p className="text-[11px] text-on-surface-variant font-medium mt-0.5">Đối chiếu dữ liệu lịch sử trong DB với kịch bản AI tối ưu.</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-semibold">
            <thead className="bg-surface-container-low text-xs text-on-surface-variant font-bold uppercase">
              <tr>
                <th className="px-6 py-4">Chỉ số chặng tàu</th>
                <th className="px-6 py-4">Lịch sử thực tế</th>
                <th className="px-6 py-4">AI đề xuất tối ưu</th>
                <th className="px-6 py-4">Mức tăng trưởng</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/30 text-sm">
              {simData ? (
                <>
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4 font-bold text-on-surface">Tổng doanh thu chặng (VND)</td>
                    <td className="px-6 py-4 font-mono text-on-surface-variant">{formatVND(simData.historical_revenue)}</td>
                    <td className="px-6 py-4 font-mono text-green-600 font-extrabold">{formatVND(simData.simulated_revenue)}</td>
                    <td className="px-6 py-4 font-mono text-green-600 font-extrabold">+{simData.revenue_lift_pct.toFixed(2)}%</td>
                  </tr>
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4 font-bold text-on-surface">Sản lượng luân chuyển (Khách-km)</td>
                    <td className="px-6 py-4 font-mono text-on-surface-variant">{formatKM(simData.historical_passenger_km)}</td>
                    <td className="px-6 py-4 font-mono text-blue-600 font-extrabold">{formatKM(simData.simulated_passenger_km)}</td>
                    <td className="px-6 py-4 font-mono text-blue-600 font-extrabold">+{simData.passenger_km_lift_pct.toFixed(2)}%</td>
                  </tr>
                </>
              ) : (
                mockTable.map((item) => (
                  <tr className="hover:bg-slate-50 transition-colors" key={item.metric}>
                    <td className="px-6 py-4 font-bold text-on-surface">{item.metric}</td>
                    <td className="px-6 py-4 text-on-surface-variant font-mono">{item.current}</td>
                    <td className="px-6 py-4 text-primary font-bold font-mono">{item.ai}</td>
                    <td className="px-6 py-4 text-outline font-mono">N/A</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Decision Action Buttons */}
      <div className="bg-white border border-outline-variant p-4 rounded-xl shadow-sm flex flex-wrap gap-3">
        <button
          onClick={() => window.alert("Đã gửi kịch bản tối ưu hóa lên hệ thống phê duyệt.")}
          className="px-4 py-2.5 bg-primary text-on-primary font-bold rounded-lg text-xs hover:brightness-110 active:scale-95 transition-all cursor-pointer"
        >
          Phê duyệt áp dụng AI
        </button>
        <button className="px-4 py-2.5 border border-outline-variant text-on-surface hover:bg-slate-50 font-bold rounded-lg text-xs transition-all cursor-pointer">
          Ghi đè thủ công
        </button>
        <button className="px-4 py-2.5 border border-outline-variant text-on-surface hover:bg-slate-50 font-bold rounded-lg text-xs transition-all cursor-pointer">
          Cập nhật giới hạn chính sách
        </button>
      </div>
    </div>
  );
}
