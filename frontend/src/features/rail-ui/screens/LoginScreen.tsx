import Link from "next/link";

export function LoginScreen() {
  return (
    <div className="login-shell">
      <section className="login-panel">
        <p className="eyebrow">SRRM Access</p>
        <h1>Đăng nhập vào Revenue Control Tower</h1>
        <p className="login-copy">
          Truy cập một không gian điều hành nhẹ nhàng, rõ ràng và đủ sâu để theo dõi tải
          chặng, báo giá, mô phỏng và kiểm toán trên cùng một luồng làm việc.
        </p>

        <div className="page-stack">
          <label className="field">
            <span>Email</span>
            <input className="input" defaultValue="revenue.manager@srrm.vn" />
          </label>
          <label className="field">
            <span>Mật khẩu</span>
            <input className="input" defaultValue="demo-password" type="password" />
          </label>
          <div className="action-row">
            <Link className="btn btn-primary" href="/dashboard">
              Đăng nhập
            </Link>
            <button className="btn btn-ghost" type="button">
              Vào nhanh với vai trò điều độ
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
