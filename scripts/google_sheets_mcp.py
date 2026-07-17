import os
import sys
from pathlib import Path

# Thêm dependencies vào virtualenv nếu chưa có
try:
    from mcp.server.fastmcp import FastMCP
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("❌ Lỗi: Thiếu thư viện. Vui lòng chạy lệnh sau để cài đặt:")
    print("   pip install mcp gspread google-auth")
    sys.exit(1)

# Khởi tạo FastMCP Server
mcp = FastMCP("SRRM Google Sheets Task Manager")

SPREADSHEET_KEY = "1z-SdPWU9hosISB2T71sYZ03-x44OzGvv"
CREDENTIALS_FILE = Path(__file__).parent.parent / "service_account.json"

@mcp.tool()
def update_task_status(task_id: str, status: str) -> str:
    """
    Cập nhật trạng thái của một Task trong Google Sheet của dự án.
    
    Args:
        task_id: Mã định danh của Task (Ví dụ: 'SRRM-001', 'SRRM-D1').
        status: Trạng thái mới (Ví dụ: 'Completed', 'In Progress', 'Pending').
    """
    if not CREDENTIALS_FILE.exists():
        return (
            f"Error: Chưa tìm thấy tệp thông tin xác thực tại: {CREDENTIALS_FILE.absolute()}\n"
            "Vui lòng tạo Service Account trên Google Cloud Console, tải tệp JSON key và đổi tên thành 'service_account.json' ở gốc dự án."
        )

    try:
        # Cấu hình quyền truy cập Google Sheets & Google Drive
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = Credentials.from_service_account_file(str(CREDENTIALS_FILE), scopes=scopes)
        client = gspread.authorize(creds)
        
        # Mở Spreadsheet và chọn sheet đầu tiên (hoặc sheet cụ thể)
        spreadsheet = client.open_by_key(SPREADSHEET_KEY)
        sheet = spreadsheet.sheet1
        
        # Tìm ô chứa mã Task ID (Ví dụ: 'SRRM-001')
        try:
            cell = sheet.find(task_id)
        except gspread.exceptions.CellNotFound:
            return f"Error: Không tìm thấy Task ID '{task_id}' trong trang tính Google Sheets."
            
        # Tìm cột Trạng thái/Status ở dòng tiêu đề (Dòng 1)
        header = sheet.row_values(1)
        status_col = None
        for i, val in enumerate(header):
            cleaned_val = val.strip().lower()
            if cleaned_val in ["trạng thái", "status", "trạng thái task", "state"]:
                status_col = i + 1
                break
                
        if not status_col:
            return "Error: Không tìm thấy cột 'Trạng thái' hoặc 'Status' ở hàng đầu tiên (Header Row)."
            
        # Thực hiện cập nhật giá trị
        sheet.update_cell(cell.row, status_col, status)
        
        return f"✅ Đã cập nhật trạng thái của Task {task_id} thành '{status}' trên Google Sheets thành công!"
        
    except Exception as e:
        return f"Error: Đã xảy ra lỗi khi kết nối Google Sheets API: {str(e)}"

if __name__ == "__main__":
    mcp.run()
