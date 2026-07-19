/** Gộp className có điều kiện, bỏ qua giá trị falsy. */
export function cn(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}

const SEAT_TYPE_MAP: Record<string, string> = {
  ngoi_mem: "Ngồi mềm điều hòa",
  giuong_nam_k6: "Giường nằm khoang 6",
  "Ngoi mem dieu hoa": "Ngồi mềm điều hòa",
  "Giuong nam khoang 6": "Giường nằm khoang 6",
  "ngoi mem dieu hoa": "Ngồi mềm điều hòa",
  "giuong nam khoang 6": "Giường nằm khoang 6",
};

/** Nhận vào mã hoặc tên thô không dấu từ backend và trả về tên tiếng Việt có dấu chuẩn */
export function getSeatTypeName(codeOrName: string | null | undefined): string {
  if (!codeOrName) return "";
  const trimmed = codeOrName.trim();
  return SEAT_TYPE_MAP[trimmed] ?? SEAT_TYPE_MAP[trimmed.toLowerCase()] ?? codeOrName;
}
