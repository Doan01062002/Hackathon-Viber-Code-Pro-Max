import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export function LoginScreen() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      <section className="bg-white border border-outline-variant rounded-xl p-8 max-w-md w-full shadow-lg relative overflow-hidden border-t-4 border-t-primary">
        <p className="text-xs font-bold text-primary uppercase tracking-widest">SRRM Access</p>
        <h1 className="text-xl font-extrabold text-on-surface mt-2 mb-4">Đăng nhập vào Revenue Control Tower</h1>
        <p className="text-xs text-on-surface-variant leading-relaxed mb-6 font-semibold">
          Truy cập một không gian điều hành nhẹ nhàng, rõ ràng và đủ sâu để theo dõi tải
          chặng, báo giá, mô phỏng và kiểm toán trên cùng một luồng làm việc.
        </p>

        <div className="space-y-4">
          <label className="block space-y-1">
            <span className="text-[10px] uppercase font-bold tracking-wider text-on-surface-variant">Email</span>
            <Input defaultValue="revenue.manager@srrm.vn" />
          </label>
          <label className="block space-y-1">
            <span className="text-[10px] uppercase font-bold tracking-wider text-on-surface-variant">Mật khẩu</span>
            <Input defaultValue="demo-password" type="password" />
          </label>
          <div className="flex gap-3 pt-4">
            <Link href="/dashboard" passHref>
              <Button className="flex-1">
                Đăng nhập
              </Button>
            </Link>
            <Button variant="outline" className="flex-1">
              Vào nhanh với vai trò điều độ
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
}
