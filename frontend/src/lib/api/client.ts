/**
 * HTTP client dùng chung — chỗ DUY NHẤT biết cách nói chuyện với backend.
 *
 * Feature không gọi fetch() trực tiếp; nó gọi apiClient. Nhờ vậy việc
 * đổi base URL, thêm auth header, hay đổi cách xử lý lỗi chỉ sửa ở đây.
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Lỗi từ API — giữ lại status để UI phân biệt 422 với 502. */
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export type RequestOptions = {
  signal?: AbortSignal;
  headers?: Record<string, string>;
};

async function request<TResponse>(
  path: string,
  init: RequestInit,
  options: RequestOptions = {},
): Promise<TResponse> {
  let res: Response;

  try {
    res = await fetch(`${BASE_URL}${path}`, {
      ...init,
      signal: options.signal,
      headers: { "Content-Type": "application/json", ...init.headers },
    });
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") throw e;
    throw new ApiError("Không kết nối được tới server", 0);
  }

  if (!res.ok) {
    throw new ApiError(await extractErrorMessage(res), res.status);
  }

  return (await res.json()) as TResponse;
}

async function extractErrorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json();
    // FastAPI trả lỗi ở "detail" — có thể là string hoặc mảng lỗi validation
    if (typeof body?.detail === "string") return body.detail;
    if (Array.isArray(body?.detail)) return body.detail[0]?.msg ?? "Dữ liệu không hợp lệ";
  } catch {
    // body không phải JSON — rơi xuống thông báo mặc định
  }
  return `Request thất bại (${res.status})`;
}

export const apiClient = {
  get: <TResponse>(path: string, options?: RequestOptions) =>
    request<TResponse>(path, { method: "GET", headers: options?.headers }, options),

  post: <TResponse>(path: string, body: unknown, options?: RequestOptions) =>
    request<TResponse>(path, { method: "POST", body: JSON.stringify(body), headers: options?.headers }, options),
};
