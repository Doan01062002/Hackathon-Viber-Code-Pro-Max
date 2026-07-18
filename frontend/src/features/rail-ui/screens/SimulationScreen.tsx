"use client";

import React, { useState, useEffect } from "react";
import { apiClient } from "@/lib/api/client";
import {
  scenarioChart as mockChart,
  simulationSummary as mockSummary,
  simulationTable as mockTable,
} from "@/features/rail-ui/mockData";
import { policyApi } from "@/features/policy/api/policyApi";
import { optimizeApi } from "@/features/optimize/api/optimizeApi";

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
  
  // State quản lý Policy Modal
  const [isPolicyModalOpen, setIsPolicyModalOpen] = useState(false);
  const [floorPrice, setFloorPrice] = useState("80000");
  const [ceilingPrice, setCeilingPrice] = useState("1500000");
  const [maxDelta, setMaxDelta] = useState(15);
  const [strategy, setStrategy] = useState("revenue");
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  
  // Load thông tin chính sách thực tế khi mở Modal
  useEffect(() => {
    async function loadActivePolicy() {
      try {
        const policyId = activeScenario || 119;
        const res = await policyApi.getPolicies();
        const activePol = res.find((p: any) => p.id === policyId);
        if (activePol) {
          setFloorPrice(Math.round(activePol.min_price).toString());
          setCeilingPrice(Math.round(activePol.max_price).toString());
          setMaxDelta(activePol.max_step_change || 15);
        }
      } catch (err) {
        console.error("Lỗi lấy thông tin chính sách:", err);
      }
    }
    if (isPolicyModalOpen) {
      loadActivePolicy();
    }
  }, [isPolicyModalOpen, activeScenario]);

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
            onClick={() => runSimulation(121)}
            className={`px-4 py-2 rounded-lg font-bold text-xs transition-all ${
              activeScenario === 121
                ? "bg-primary text-on-primary"
                : "bg-white border border-outline-variant text-on-surface hover:bg-slate-50"
            }`}
          >
            Chính sách Huế - Đà Nẵng
          </button>
          <button
            onClick={() => runSimulation(119)}
            className={`px-4 py-2 rounded-lg font-bold text-xs transition-all ${
              activeScenario === 119
                ? "bg-primary text-on-primary"
                : "bg-white border border-outline-variant text-on-surface hover:bg-slate-50"
            }`}
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
              <span className="text-[9px] text-on-surface-variant font-bold uppercase">Tăng trưởng doanh thu</span>
              <p className="font-black mt-1 text-green-600 text-sm">
                {simData ? `+${simData.revenue_lift_pct.toFixed(2)}%` : mockSummary.revenueLift}
              </p>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-outline-variant/30 text-xs">
              <span className="text-[9px] text-on-surface-variant font-bold uppercase">Tăng trưởng sản lượng</span>
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
            Biểu đồ so sánh kịch bản
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
          onClick={async () => {
            try {
              setLoading(true);
              const res = await optimizeApi.resolveOptimization(1);
              setToastMessage(`Phê duyệt thành công! Job ID: ${res.job_id.substring(0, 8)}`);
              setTimeout(() => setToastMessage(null), 4000);
              await runSimulation(activeScenario ?? undefined);
            } catch (err) {
              console.error("Lỗi phê duyệt tối ưu hóa:", err);
              setToastMessage("Yêu cầu phê duyệt thất bại.");
              setTimeout(() => setToastMessage(null), 3000);
            } finally {
              setLoading(false);
            }
          }}
          disabled={loading}
          className="px-4 py-2.5 bg-primary text-on-primary font-bold rounded-lg text-xs hover:brightness-110 active:scale-95 transition-all disabled:opacity-50 cursor-pointer"
        >
          {loading ? "Đang phê duyệt..." : "Phê duyệt áp dụng AI"}
        </button>
        <button className="px-4 py-2.5 border border-outline-variant text-on-surface hover:bg-slate-50 font-bold rounded-lg text-xs transition-all cursor-pointer">
          Ghi đè thủ công
        </button>
        <button
          onClick={() => setIsPolicyModalOpen(true)}
          className="px-4 py-2.5 border border-outline-variant text-on-surface hover:bg-slate-50 font-bold rounded-lg text-xs transition-all cursor-pointer"
        >
          Cập nhật giới hạn chính sách
        </button>
      </div>

      {/* Policy Limits Modal */}
      {isPolicyModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-outline-variant rounded-2xl max-w-md w-full shadow-2xl p-6 relative overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <h3 className="font-extrabold text-base text-on-surface flex items-center gap-2 mb-2">
              <span className="material-symbols-outlined text-primary">rule_settings</span>
              Cập nhật giới hạn chính sách
            </h3>
            <p className="text-xs text-on-surface-variant font-medium mb-6">
              Điều chỉnh các tham số biên độ giá trần/sàn và chiến lược áp dụng cho động cơ định giá.
            </p>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <label className="block space-y-1">
                  <span className="text-[10px] uppercase font-bold tracking-wider text-on-surface-variant">Giá sàn (Min VND)</span>
                  <input
                    type="number"
                    value={floorPrice}
                    onChange={(e) => setFloorPrice(e.target.value)}
                    className="w-full bg-slate-50 border border-outline-variant rounded-lg py-2 px-3 text-xs font-semibold focus:ring-1 focus:ring-primary outline-none"
                  />
                </label>
                <label className="block space-y-1">
                  <span className="text-[10px] uppercase font-bold tracking-wider text-on-surface-variant">Giá trần (Max VND)</span>
                  <input
                    type="number"
                    value={ceilingPrice}
                    onChange={(e) => setCeilingPrice(e.target.value)}
                    className="w-full bg-slate-50 border border-outline-variant rounded-lg py-2 px-3 text-xs font-semibold focus:ring-1 focus:ring-primary outline-none"
                  />
                </label>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-center text-[10px] uppercase font-bold text-on-surface-variant">
                  <span>Biến động tối đa hàng ngày</span>
                  <span className="text-primary font-mono font-bold text-xs">{maxDelta}%</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="30"
                  value={maxDelta}
                  onChange={(e) => setMaxDelta(Number(e.target.value))}
                  className="w-full accent-primary h-1.5 bg-slate-100 rounded-full appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-[9px] text-on-surface-variant/60 font-bold font-mono">
                  <span>Tối thiểu: 5%</span>
                  <span>Tối đa: 30%</span>
                </div>
              </div>

              <div className="space-y-2">
                <span className="text-[10px] uppercase font-bold tracking-wider text-on-surface-variant block">Chiến lược tối ưu hóa</span>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setStrategy("revenue")}
                    className={`p-3 rounded-lg border text-left flex flex-col justify-between transition-all ${
                      strategy === "revenue"
                        ? "border-primary bg-primary/5 ring-1 ring-primary"
                        : "border-outline-variant hover:bg-slate-50"
                    }`}
                  >
                    <span className="text-xs font-bold text-on-surface">Tối đa hóa doanh thu</span>
                    <span className="text-[9px] text-on-surface-variant/80 mt-1 font-medium leading-tight">Ưu tiên bán giá cao chặng dài</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setStrategy("load")}
                    className={`p-3 rounded-lg border text-left flex flex-col justify-between transition-all ${
                      strategy === "load"
                        ? "border-primary bg-primary/5 ring-1 ring-primary"
                        : "border-outline-variant hover:bg-slate-50"
                    }`}
                  >
                    <span className="text-xs font-bold text-on-surface">Tối ưu hệ số lấp đầy</span>
                    <span className="text-[9px] text-on-surface-variant/80 mt-1 font-medium leading-tight">Ưu tiên lấp đầy chỗ trống ngắn chặng</span>
                  </button>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-6 mt-4 border-t border-outline-variant/30">
              <button
                type="button"
                onClick={() => setIsPolicyModalOpen(false)}
                className="px-4 py-2 border border-outline-variant text-on-surface hover:bg-slate-50 font-bold rounded-lg text-xs transition-all cursor-pointer"
              >
                Hủy bỏ
              </button>
              <button
                type="button"
                onClick={async () => {
                  try {
                    const policyId = activeScenario || 119;
                    await policyApi.updatePolicy(policyId, {
                      min_price: Number(floorPrice),
                      max_price: Number(ceilingPrice),
                      max_step_change: maxDelta,
                    });
                    
                    setIsPolicyModalOpen(false);
                    setToastMessage("Cập nhật giới hạn chính sách thành công!");
                    setTimeout(() => setToastMessage(null), 3000);
                    
                    runSimulation(activeScenario ?? undefined);
                  } catch (err) {
                    console.error("Lỗi lưu chính sách:", err);
                    setToastMessage("Lưu chính sách thất bại.");
                    setTimeout(() => setToastMessage(null), 3000);
                  }
                }}
                className="px-4 py-2 bg-primary text-on-primary font-bold rounded-lg text-xs hover:brightness-110 active:scale-95 transition-all cursor-pointer"
              >
                Lưu thay đổi
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Success Toast */}
      {toastMessage && (
        <div className="fixed top-6 left-1/2 -translate-x-1/2 z-50 bg-slate-900 text-white text-xs font-bold px-4 py-2.5 rounded-xl shadow-2xl border border-slate-800 flex items-center gap-2 animate-in slide-in-from-top-4 duration-200">
          <span className="material-symbols-outlined text-green-400 text-sm">check_circle</span>
          {toastMessage}
        </div>
      )}
    </div>
  );
}
