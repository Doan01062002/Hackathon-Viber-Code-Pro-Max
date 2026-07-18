"use client";

import React, { useState, useEffect } from "react";
import { apiClient } from "@/lib/api/client";
import { auditLogs as mockLogs } from "@/features/rail-ui/mockData";

interface AuditLogItem {
  id: number;
  actor: string;
  action: string;
  entity_type: string;
  entity_id: number | null;
  before_data: any;
  after_data: any;
  created_at: string;
}

export function AuditScreen() {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Bộ lọc tìm kiếm
  const [actorFilter, setActorFilter] = useState("");
  const [actionFilter, setActionFilter] = useState("");

  useEffect(() => {
    async function fetchLogs() {
      try {
        setLoading(true);
        setError(null);
        // Gọi API nhật ký kiểm toán với vai trò revenue_manager
        const data = await apiClient.get<AuditLogItem[]>("/api/v1/audit/logs", {
          headers: { "X-User-Role": "revenue_manager" }
        });
        setLogs(data);
      } catch (err) {
        console.warn("Không tải được API kiểm toán, sử dụng fallback:", err);
        setError("Không thể lấy dữ liệu nhật ký kiểm toán thời gian thực.");
      } finally {
        setLoading(false);
      }
    }
    fetchLogs();
  }, []);

  const logsToRender = logs.length > 0 ? logs : null;

  // Lọc dữ liệu hiển thị dựa trên bộ gõ tìm kiếm
  const getFilteredLogs = () => {
    if (!logsToRender) {
      return mockLogs.filter(item => {
        const matchActor = actorFilter === "" || item.actor.toLowerCase().includes(actorFilter.toLowerCase());
        const matchAction = actionFilter === "" || item.action.toLowerCase().includes(actionFilter.toLowerCase());
        return matchActor && matchAction;
      });
    }
    return logs.filter(item => {
      const matchActor = actorFilter === "" || item.actor.toLowerCase().includes(actorFilter.toLowerCase());
      const matchAction = actionFilter === "" || item.action.toLowerCase().includes(actionFilter.toLowerCase());
      return matchActor && matchAction;
    });
  };

  const filteredLogs = getFilteredLogs();
  const activeLog = logsToRender ? logsToRender[selectedIndex] : null;

  const beforeJson = activeLog 
    ? JSON.stringify(activeLog.before_data, null, 2) 
    : (mockLogs[selectedIndex]?.before ?? "{}");
  const afterJson = activeLog 
    ? JSON.stringify(activeLog.after_data, null, 2) 
    : (mockLogs[selectedIndex]?.after ?? "{}");

  return (
    <div className="space-y-6">

      {error && (
        <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded-lg text-yellow-700 text-xs font-semibold">
          ⚠️ Cảnh báo: {error} Đang hiển thị nhật ký Demo cục bộ.
        </div>
      )}

      {/* Filter Bar */}
      <div className="bg-white border border-outline-variant p-4 rounded-xl shadow-sm grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
        <div className="space-y-1">
          <label className="text-[10px] uppercase font-bold tracking-wider text-on-surface-variant">Người thao tác (Actor)</label>
          <input
            className="w-full bg-surface-container-low border border-outline-variant rounded-lg py-1.5 px-3 text-xs font-semibold outline-none focus:ring-1 focus:ring-primary"
            placeholder="Nhập tên người dùng..."
            value={actorFilter}
            onChange={(e) => setActorFilter(e.target.value)}
          />
        </div>
        <div className="space-y-1">
          <label className="text-[10px] uppercase font-bold tracking-wider text-on-surface-variant">Hành động</label>
          <input
            className="w-full bg-surface-container-low border border-outline-variant rounded-lg py-1.5 px-3 text-xs font-semibold outline-none focus:ring-1 focus:ring-primary"
            placeholder="Nhập hành động (vd: Cập nhật)..."
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
          />
        </div>
        <div className="space-y-1">
          <label className="text-[10px] uppercase font-bold tracking-wider text-on-surface-variant">Vai trò xác thực</label>
          <input
            className="w-full bg-slate-100 border border-outline-variant rounded-lg py-1.5 px-3 text-xs font-semibold outline-none text-on-surface-variant"
            value="Revenue Manager"
            readOnly
          />
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-white border border-outline-variant rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-outline-variant flex justify-between items-center bg-white">
          <h3 className="font-bold text-sm text-on-surface">Audit Logs</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-surface-container-low text-xs text-on-surface-variant font-bold uppercase">
              <tr>
                <th className="px-6 py-4">Người dùng (Actor)</th>
                <th className="px-6 py-4">Hành động thực hiện</th>
                <th className="px-6 py-4">Thực thể bị tác động (Entity)</th>
                <th className="px-6 py-4 text-right">Thời gian ghi nhận</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/30 text-sm">
              {filteredLogs.map((item, idx) => {
                const isSelected = idx === selectedIndex;
                return (
                  <tr
                    key={idx}
                    onClick={() => setSelectedIndex(idx)}
                    className={`cursor-pointer transition-colors duration-150 ${
                      isSelected
                        ? "bg-primary/5 font-bold border-l-4 border-l-primary"
                        : "hover:bg-surface-container-low"
                    }`}
                  >
                    <td className="px-6 py-4 text-primary font-bold">
                      {logsToRender ? (item as any).actor : (item as any).actor}
                    </td>
                    <td className="px-6 py-4 text-on-surface font-semibold">
                      {logsToRender ? (item as any).action : (item as any).action}
                    </td>
                    <td className="px-6 py-4 text-on-surface-variant font-medium">
                      {logsToRender ? `${(item as any).entity_type} ID: ${(item as any).entity_id}` : (item as any).entity}
                    </td>
                    <td className="px-6 py-4 text-right text-on-surface-variant font-mono font-medium">
                      {logsToRender
                        ? new Date((item as any).created_at).toLocaleString("vi-VN")
                        : (item as any).time}
                    </td>
                  </tr>
                );
              })}
              {filteredLogs.length === 0 && (
                <tr>
                  <td colSpan={4} className="text-center text-xs text-on-surface-variant font-semibold py-8">
                    Không tìm thấy nhật ký kiểm toán nào khớp bộ lọc.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* JSON Comparison panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-outline-variant rounded-xl p-4 shadow-sm">
          <h4 className="font-bold text-xs text-on-surface uppercase tracking-wider mb-2">Dữ liệu trước thay đổi (Before Data)</h4>
          <pre className="bg-slate-900 text-red-400 p-4 rounded-lg font-mono text-xs overflow-x-auto leading-relaxed max-h-64">
            {beforeJson}
          </pre>
        </div>
        <div className="bg-white border border-outline-variant rounded-xl p-4 shadow-sm">
          <h4 className="font-bold text-xs text-on-surface uppercase tracking-wider mb-2">Dữ liệu sau thay đổi (After Data)</h4>
          <pre className="bg-slate-900 text-green-400 p-4 rounded-lg font-mono text-xs overflow-x-auto leading-relaxed max-h-64">
            {afterJson}
          </pre>
        </div>
      </div>
    </div>
  );
}
