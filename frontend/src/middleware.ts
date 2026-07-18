import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(req: NextRequest) {
  const authHeader = req.headers.get('authorization');
  
  if (authHeader) {
    const auth = authHeader.split(' ')[1];
    try {
      // Sử dụng atob (hỗ trợ Edge Runtime của Next.js) để giải mã Base64
      const decoded = atob(auth);
      const [user, pwd] = decoded.split(':');
      
      // Bạn có thể sửa tên đăng nhập và mật khẩu mong muốn tại đây
      if (user === 'admin' && pwd === 'srrm-secure-demo') {
        return NextResponse.next();
      }
    } catch (e) {
      // Bỏ qua nếu lỗi giải mã
    }
  }
  
  // Trả về mã lỗi 401 Unauthorized để trình duyệt hiển thị hộp thoại đăng nhập Basic Auth
  return new NextResponse('Authentication Required', {
    status: 401,
    headers: {
      'WWW-Authenticate': 'Basic realm="SRRM Secure Portal"',
    },
  });
}

export const config = {
  matcher: [
    /*
     * Áp dụng bảo mật cho toàn bộ các trang ngoại trừ:
     * - api (các API nội bộ của Next.js)
     * - _next/static (các file tĩnh của css/js)
     * - _next/image (tối ưu hóa ảnh)
     * - favicon.ico (icon trang web)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
