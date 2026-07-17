"use client";

import { useState, useEffect } from "react";
import { SectionCard } from "@/features/rail-ui/components/Primitives";
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
    <div className="page-stack">
      {error && (
        <div className="banner banner-warning" style={{ backgroundColor: "#3a2a18", borderLeft: "4px solid #d97706", padding: "12px", borderRadius: "6px", color: "#f59e0b", fontSize: "14px", marginBottom: "8px" }}>
          ⚠️ <strong>Cảnh báo:</strong> {error} Đang hiển thị nhật ký Demo cục bộ.
        </div>
      )}

      <SectionCard title="Bộ lọc kiểm toán" subtitle="Tìm kiếm nhanh nhật ký can thiệp theo người thao tác (actor) và hành động.">
        <div className="form-grid">
          <label className="field">
            <span>Người thao tác (Actor)</span>
            <input 
              className="input" 
              placeholder="Nhập tên người dùng..." 
              value={actorFilter}
              onChange={(e) => setActorFilter(e.target.value)}
              style={{ backgroundColor: "#1e1e24", color: "#fff", border: "1px solid #333", borderRadius: "4px", padding: "8px" }}
            />
          </label>
          <label className="field">
            <span>Hành động</span>
            <input 
              className="input" 
              placeholder="Nhập hành động (vd: Cập nhật)..." 
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              style={{ backgroundColor: "#1e1e24", color: "#fff", border: "1px solid #333", borderRadius: "4px", padding: "8px" }}
            />
          </label>
          <label className="field">
            <span>Vai trò xác thực</span>
            <input className="input" value="Revenue Manager" readOnly style={{ backgroundColor: "#151518", color: "#888" }} />
          </label>
        </div>
      </SectionCard>

      <SectionCard
        title="Bảng nhật ký kiểm toán hệ thống"
        subtitle="Danh sách các lần điều chỉnh hạn ngạch, thay đổi giá trần/sàn được tự động ghi nhận."
      >
        <div className="table-wrap">
          <table className="data-table audit-table">
            <thead>
              <tr>
                <th>Người dùng (Actor)</th>
                <th>Hành động thực hiện</th>
                <th>Thực thể bị tác động (Entity)</th>
                <th>Thời gian ghi nhận</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.map((item, idx) => {
                const isSelected = idx === selectedIndex;
                return (
                  <tr 
                    key={idx} 
                    onClick={() => setSelectedIndex(idx)}
                    style={{ cursor: "pointer", backgroundColor: isSelected ? "#2d2d3a" : "transparent", transition: "background-color 0.2s" }}
                  >
                    <th scope="row" style={{ color: isSelected ? "#10b981" : "#fff" }}>
                      {logsToRender ? (item as any).actor : (item as any).actor}
                    </th>
                    <td>{logsToRender ? (item as any).action : (item as any).action}</td>
                    <td>{logsToRender ? `${(item as any).entity_type} ID: ${(item as any).entity_id}` : (item as any).entity}</td>
                    <td>
                      {logsToRender 
                        ? new Date((item as any).created_at).toLocaleString() 
                        : (item as any).time}
                    </td>
                  </tr>
                );
              })}
              {filteredLogs.length === 0 && (
                <tr>
                  <td colSpan={4} style={{ textAlign: "center", color: "#888", padding: "20px" }}>
                    Không tìm thấy nhật ký kiểm toán nào khớp bộ lọc.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </SectionCard>

      <div className="two-up">
        <SectionCard title="Dữ liệu trước thay đổi (Before Data)" subtitle="Trạng thái cấu hình ban đầu trước khi tác vụ diễn ra.">
          <pre className="code-block" style={{ backgroundColor: "#111", color: "#f87171", padding: "16px", borderRadius: "6px", fontFamily: "monospace", fontSize: "13px", overflowX: "auto" }}>
            {beforeJson}
          </pre>
        </SectionCard>
        <SectionCard title="Dữ liệu sau thay đổi (After Data)" subtitle="Giá trị cấu hình mới được áp dụng thành công.">
          <pre className="code-block" style={{ backgroundColor: "#111", color: "#34d399", padding: "16px", borderRadius: "6px", fontFamily: "monospace", fontSize: "13px", overflowX: "auto" }}>
            {afterJson}
          </pre>
        </SectionCard>
      </div>
    </div>
  );
}
