from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse

from backend.services.checkdata_service import CheckDataService
from backend.views.checkdata_view import (
    DatabaseSummaryResponse,
    DatabaseTableCountResponse,
    TableCountResponse,
    TableDataResponse,
)

router = APIRouter()


def get_checkdata_service() -> CheckDataService:
    return CheckDataService()


@router.get("/checkdata", response_class=HTMLResponse)
async def checkdata_page() -> HTMLResponse:
    return HTMLResponse(CHECKDATA_HTML)


@router.get("/checkdata/api/table-count", response_model=DatabaseTableCountResponse)
async def count_database_tables(
    service: Annotated[CheckDataService, Depends(get_checkdata_service)],
) -> DatabaseTableCountResponse:
    return service.count_tables()


@router.get("/checkdata/api/tables", response_model=DatabaseSummaryResponse)
async def list_database_tables(
    service: Annotated[CheckDataService, Depends(get_checkdata_service)],
    include_counts: bool = False,
) -> DatabaseSummaryResponse:
    return service.list_tables(include_counts=include_counts)


@router.get("/checkdata/api/tables/{table_name}", response_model=TableDataResponse)
async def get_table_data(
    table_name: str,
    service: Annotated[CheckDataService, Depends(get_checkdata_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TableDataResponse:
    return service.get_table_data(table_name=table_name, limit=limit, offset=offset)


@router.get("/checkdata/api/tables/{table_name}/count", response_model=TableCountResponse)
async def get_table_count(
    table_name: str,
    service: Annotated[CheckDataService, Depends(get_checkdata_service)],
) -> TableCountResponse:
    return service.count_rows(table_name)


CHECKDATA_HTML = """
<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SRRM Database Check</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f3f6f8;
      --panel: #ffffff;
      --ink: #102033;
      --muted: #647184;
      --line: #d9e1ea;
      --line-strong: #bdc9d7;
      --brand: #0f766e;
      --brand-dark: #115e59;
      --brand-soft: #e7f4f2;
      --blue-soft: #eef6ff;
      --danger: #b42318;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
    }

    * { box-sizing: border-box; }
    body { margin: 0; background: var(--bg); color: var(--ink); }
    body::before { content: ""; display: block; height: 10px; background: var(--brand-dark); }

    main { width: min(1180px, calc(100% - 32px)); margin: 0 auto; padding: 24px 0 44px; }
    header { display: flex; justify-content: space-between; gap: 16px; align-items: center; margin-bottom: 18px; }
    h1 { margin: 0; font-size: 28px; line-height: 1.15; letter-spacing: 0; }
    h2 { margin: 0; font-size: 16px; letter-spacing: 0; }
    p { margin: 6px 0 0; color: var(--muted); line-height: 1.5; }
    label { display: block; margin-bottom: 6px; color: #4a5a6e; font-size: 12px; font-weight: 700; }

    button, select, input {
      height: 38px;
      border: 1px solid var(--line-strong);
      border-radius: 7px;
      background: #fff;
      color: var(--ink);
      font: inherit;
    }
    input, select { width: 100%; padding: 0 10px; }
    button { padding: 0 13px; cursor: pointer; font-weight: 700; }
    button:hover { background: #f8fbfc; border-color: #93a6b8; }
    button:disabled { cursor: not-allowed; opacity: .55; }
    .primary { background: var(--brand); color: #fff; border-color: var(--brand); }
    .primary:hover { background: var(--brand-dark); border-color: var(--brand-dark); }
    .ghost { background: #fff; }

    .top-actions { display: flex; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }
    .layout { display: grid; grid-template-columns: 320px 1fr; gap: 18px; align-items: start; }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 8px 22px rgb(16 32 51 / 6%);
    }
    .panel-head { padding: 16px 16px 0; }
    .panel-body { padding: 16px; }

    .status {
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      padding: 5px 10px;
      border-radius: 999px;
      background: var(--blue-soft);
      color: #275071;
      font-size: 12px;
      font-weight: 700;
    }
    .status.error { background: #fff0f0; color: var(--danger); }

    .metrics { display: grid; gap: 10px; }
    .metric {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
      align-items: center;
      padding: 13px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfd;
    }
    .metric span { color: var(--muted); font-size: 12px; font-weight: 700; }
    .metric strong { font-size: 28px; line-height: 1; }

    .action-stack { display: grid; gap: 10px; margin-top: 14px; }
    .button-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .select-wrap { margin-top: 14px; }
    .hint { color: var(--muted); font-size: 12px; line-height: 1.45; }
    .hint strong { color: var(--ink); }

    .query-bar {
      display: grid;
      grid-template-columns: minmax(220px, 1fr) 92px 92px auto;
      gap: 10px;
      align-items: end;
      padding: 16px;
      border-bottom: 1px solid var(--line);
    }
    .result-head {
      display: flex;
      justify-content: space-between;
      gap: 14px;
      align-items: center;
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
      background: #fbfcfd;
    }
    .current-table { margin: 3px 0 0; color: var(--muted); font-size: 12px; }
    .scroll { max-height: 62vh; overflow: auto; }

    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td {
      border-bottom: 1px solid #e7edf3;
      padding: 10px 12px;
      text-align: left;
      vertical-align: top;
      max-width: 300px;
      overflow-wrap: anywhere;
    }
    th {
      position: sticky;
      top: 0;
      z-index: 1;
      background: #f4f8fb;
      color: #2e4156;
      font-size: 12px;
      font-weight: 800;
    }
    tr:hover td { background: #f8fbfc; }

    .empty {
      display: grid;
      place-items: center;
      min-height: 310px;
      padding: 32px;
      text-align: center;
      color: var(--muted);
    }
    .empty strong { display: block; margin-bottom: 6px; color: var(--ink); font-size: 16px; }

    @media (max-width: 900px) {
      header { display: block; }
      .top-actions { justify-content: flex-start; margin-top: 14px; }
      .layout { grid-template-columns: 1fr; }
      .query-bar { grid-template-columns: 1fr 1fr; }
      .query-bar .table-field { grid-column: 1 / -1; }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>SRRM Database Check</h1>
        <p>Công cụ xem database nhanh. Trang không tự query, bạn bấm đúng thao tác cần dùng.</p>
      </div>
      <div class="top-actions">
        <button type="button" class="ghost" id="countTablesBtn">Đếm bảng</button>
        <button type="button" class="primary" id="loadTablesBtn">Tải danh sách bảng</button>
      </div>
    </header>

    <section class="layout">
      <aside class="panel">
        <div class="panel-head">
          <h2>Tổng quan</h2>
          <p class="hint">Các số liệu chỉ được đọc khi bạn bấm nút tương ứng.</p>
        </div>
        <div class="panel-body">
          <div class="metrics">
            <div class="metric">
              <span>Tổng số bảng</span>
              <strong id="tableCount">-</strong>
            </div>
            <div class="metric">
              <span>Số dòng bảng đang chọn</span>
              <strong id="selectedCount">-</strong>
            </div>
          </div>

          <div class="action-stack">
            <div class="button-row">
              <button type="button" class="ghost" id="countRowsBtn">Đếm dòng</button>
              <button type="button" class="ghost" id="clearBtn">Xóa kết quả</button>
            </div>
          </div>

          <div class="select-wrap">
            <label for="tableSelect">Chọn bảng đã tải</label>
            <select id="tableSelect">
              <option value="">Chưa tải danh sách</option>
            </select>
            <p class="hint" id="tableMeta">Có thể gõ tên bảng trực tiếp ở khung bên phải.</p>
          </div>
        </div>
      </aside>

      <section class="panel">
        <div class="query-bar">
          <div class="table-field">
            <label for="tableNameInput">Tên bảng</label>
            <input id="tableNameInput" type="text" placeholder="vd: stations" autocomplete="off" />
          </div>
          <div>
            <label for="limitInput">Limit</label>
            <input id="limitInput" type="number" min="1" max="100" value="20" />
          </div>
          <div>
            <label for="offsetInput">Offset</label>
            <input id="offsetInput" type="number" min="0" value="0" />
          </div>
          <button type="button" class="primary" id="loadBtn">Xem dữ liệu</button>
        </div>

        <div class="result-head">
          <div>
            <h2>Kết quả</h2>
            <p class="current-table" id="currentTable">Chưa chọn bảng nào.</p>
          </div>
          <span class="status" id="statusText">San sang</span>
        </div>

        <div class="scroll" id="tableWrap">
          <div class="empty">
            <div>
              <strong>Nhập tên bảng rồi bấm Xem dữ liệu</strong>
              <span>Nếu chưa nhớ tên bảng, bấm Tải danh sách bảng trước.</span>
            </div>
          </div>
        </div>
      </section>
    </section>
  </main>

  <script>
    const tableSelect = document.getElementById("tableSelect");
    const tableCount = document.getElementById("tableCount");
    const selectedCount = document.getElementById("selectedCount");
    const tableMeta = document.getElementById("tableMeta");
    const tableWrap = document.getElementById("tableWrap");
    const statusText = document.getElementById("statusText");
    const tableNameInput = document.getElementById("tableNameInput");
    const limitInput = document.getElementById("limitInput");
    const offsetInput = document.getElementById("offsetInput");
    const currentTable = document.getElementById("currentTable");
    const buttons = Array.from(document.querySelectorAll("button"));

    async function fetchJson(url) {
      const response = await fetch(url);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Request failed");
      return data;
    }

    function setStatus(text, isError = false) {
      statusText.textContent = text;
      statusText.className = isError ? "status error" : "status";
    }

    async function runAction(label, action) {
      try {
        buttons.forEach((button) => { button.disabled = true; });
        setStatus(label);
        await action();
      } catch (error) {
        setStatus(error.message, true);
      } finally {
        buttons.forEach((button) => { button.disabled = false; });
      }
    }

    function getTableName() {
      return tableNameInput.value.trim() || tableSelect.value.trim();
    }

    function renderRows(data) {
      if (!data.rows.length) {
        tableWrap.innerHTML = '<div class="empty"><div><strong>Không có dòng nào ở offset này</strong><span>Thử giảm offset hoặc kiểm tra lại tên bảng.</span></div></div>';
        return;
      }

      const head = data.columns.map((col) => `<th>${escapeHtml(col)}</th>`).join("");
      const body = data.rows.map((row) => {
        const cells = data.columns.map((col) => `<td>${escapeHtml(formatValue(row[col]))}</td>`).join("");
        return `<tr>${cells}</tr>`;
      }).join("");
      tableWrap.innerHTML = `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
    }

    function formatValue(value) {
      if (value === null || value === undefined) return "";
      if (typeof value === "object") return JSON.stringify(value);
      return String(value);
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    async function countTables() {
      const data = await fetchJson("/checkdata/api/table-count");
      tableCount.textContent = data.table_count;
      setStatus("Đã đếm số bảng");
    }

    async function loadTables() {
      const data = await fetchJson("/checkdata/api/tables?include_counts=false");
      tableCount.textContent = data.table_count;
      tableSelect.innerHTML = data.tables.length
        ? data.tables.map((table) => `<option value="${escapeHtml(table.name)}">${escapeHtml(table.name)}</option>`).join("")
        : '<option value="">Database chưa có bảng</option>';

      if (data.tables.length) {
        tableNameInput.value = tableNameInput.value || data.tables[0].name;
        tableMeta.innerHTML = `<strong>${data.tables.length}</strong> bảng đã tải. Chưa đếm row count từng bảng.`;
        setStatus("Đã tải danh sách bảng");
      } else {
        selectedCount.textContent = "0";
        tableWrap.innerHTML = '<div class="empty"><div><strong>Database chưa có bảng</strong><span>Hãy kiểm tra migration hoặc seed data.</span></div></div>';
        setStatus("Không có bảng");
      }
    }

    async function countSelectedRows() {
      const tableName = getTableName();
      if (!tableName) throw new Error("Nhập hoặc chọn một bảng trước.");

      const count = await fetchJson(`/checkdata/api/tables/${encodeURIComponent(tableName)}/count`);
      selectedCount.textContent = count.row_count;
      currentTable.textContent = `Đang chọn: ${tableName}`;
      setStatus("Đã đếm số dòng");
    }

    async function loadSelectedTable() {
      const tableName = getTableName();
      if (!tableName) throw new Error("Nhập hoặc chọn một bảng trước.");

      const limit = Math.min(Math.max(Number(limitInput.value) || 20, 1), 100);
      const offset = Math.max(Number(offsetInput.value) || 0, 0);
      limitInput.value = limit;
      offsetInput.value = offset;

      const rows = await fetchJson(`/checkdata/api/tables/${encodeURIComponent(tableName)}?limit=${limit}&offset=${offset}`);
      tableNameInput.value = tableName;
      currentTable.textContent = `${tableName} - đang hiển thị ${rows.row_count} dòng, ${rows.columns.length} cột`;
      tableMeta.textContent = `Limit ${limit}, offset ${offset}. Tổng số dòng chỉ đếm khi bấm Đếm dòng.`;
      renderRows(rows);
      setStatus("Đã tải dữ liệu mẫu");
    }

    function clearResult() {
      selectedCount.textContent = "-";
      currentTable.textContent = "Chưa chọn bảng nào.";
      tableWrap.innerHTML = '<div class="empty"><div><strong>Nhập tên bảng rồi bấm Xem dữ liệu</strong><span>Nếu chưa nhớ tên bảng, bấm Tải danh sách bảng trước.</span></div></div>';
      setStatus("Đã xóa kết quả");
    }

    document.getElementById("countTablesBtn").addEventListener("click", () => runAction("Đang đếm bảng...", countTables));
    document.getElementById("loadTablesBtn").addEventListener("click", () => runAction("Đang tải danh sách bảng...", loadTables));
    document.getElementById("countRowsBtn").addEventListener("click", () => runAction("Đang đếm dòng...", countSelectedRows));
    document.getElementById("loadBtn").addEventListener("click", () => runAction("Đang tải dữ liệu...", loadSelectedTable));
    document.getElementById("clearBtn").addEventListener("click", clearResult);
    tableSelect.addEventListener("change", () => {
      tableNameInput.value = tableSelect.value;
      selectedCount.textContent = "-";
      currentTable.textContent = tableSelect.value ? `Đang chọn: ${tableSelect.value}` : "Chưa chọn bảng nào.";
      tableWrap.innerHTML = '<div class="empty"><div><strong>Đã chọn bảng</strong><span>Bấm Đếm dòng hoặc Xem dữ liệu để query database.</span></div></div>';
      setStatus("Đã chọn bảng");
    });
  </script>
</body>
</html>
"""
