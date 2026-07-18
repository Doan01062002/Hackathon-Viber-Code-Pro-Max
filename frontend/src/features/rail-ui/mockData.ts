export type NavItem = {
  href: string;
  label: string;
  icon: string;
  group: "passenger" | "admin";
};

export const navItems: NavItem[] = [
  { href: "/booking", label: "Đặt vé tàu", icon: "confirmation_number", group: "passenger" },
  { href: "/dashboard", label: "Tổng quan", icon: "dashboard", group: "admin" },
  { href: "/quote", label: "Báo giá", icon: "price", group: "admin" },
  { href: "/simulation", label: "Mô phỏng", icon: "simulation", group: "admin" },
  { href: "/alerts", label: "Dự đoán & Cảnh báo", icon: "alert", group: "admin" },
  { href: "/audit", label: "Kiểm toán", icon: "audit", group: "admin" },
  { href: "/train-layout", label: "Toa tàu", icon: "train", group: "admin" },
];

export const topMetrics = [
  { label: "Tải trung bình", value: "78%", detail: "Tăng 4 điểm so với hôm qua", tone: "good" },
  { label: "Doanh thu dự kiến", value: "2,84 tỷ", detail: "Đạt 103% kế hoạch ngày", tone: "neutral" },
  { label: "Chặng rủi ro", value: "01", detail: "Huế → Đà Nẵng đang gần đầy", tone: "warn" },
  { label: "Cảnh báo mở", value: "12", detail: "03 cảnh báo cần xử lý ngay", tone: "danger" },
];

export const heatmapRows = [
  { segment: "Hà Nội → Vinh", slots: [62, 68, 71, 76, 81, 79] },
  { segment: "Vinh → Đồng Hới", slots: [58, 64, 66, 72, 75, 74] },
  { segment: "Đồng Hới → Huế", slots: [73, 79, 82, 84, 88, 86] },
  { segment: "Huế → Đà Nẵng", slots: [88, 92, 95, 97, 99, 96] },
  { segment: "Đà Nẵng → Nha Trang", slots: [67, 71, 76, 79, 82, 80] },
  { segment: "Nha Trang → Sài Gòn", slots: [59, 63, 68, 70, 74, 72] },
];

export const bookingCurve = [
  { day: "D-30", actual: 14, forecast: 18 },
  { day: "D-20", actual: 28, forecast: 31 },
  { day: "D-10", actual: 48, forecast: 52 },
  { day: "D-7", actual: 58, forecast: 61 },
  { day: "D-3", actual: 74, forecast: 76 },
  { day: "D-1", actual: 88, forecast: 91 },
];

export const odMatrix = [
  ["", "Vinh", "Huế", "Đà Nẵng", "Nha Trang", "Sài Gòn"],
  ["Hà Nội", "120", "86", "94", "70", "112"],
  ["Vinh", "-", "58", "44", "36", "62"],
  ["Huế", "-", "-", "81", "39", "47"],
  ["Đà Nẵng", "-", "-", "-", "55", "63"],
];

export const gapSuggestions = [
  {
    route: "Vinh → Huế",
    seatType: "Giường nằm K6",
    benefit: "+17 chỗ khả dụng",
    priority: "Cao",
    reason: "Có 3 khoảng trống liên tiếp trong toa B2 sau khi mở lại quota ngắn.",
  },
  {
    route: "Đồng Hới → Đà Nẵng",
    seatType: "Ngồi mềm",
    benefit: "+11 chỗ khả dụng",
    priority: "Trung bình",
    reason: "Nhu cầu ngắn hạn tăng nhưng hàng ghế giữa toa vẫn chưa được tận dụng.",
  },
  {
    route: "Nha Trang → Sài Gòn",
    seatType: "Ngồi mềm",
    benefit: "+9 chỗ khả dụng",
    priority: "Theo dõi",
    reason: "Tốc độ bán thấp hơn dự báo nên có thể nới bán để tăng lấp đầy cuối chặng.",
  },
];

export const simulationSummary = {
  policy: "Cuối tuần tháng 7 nhu cầu cao",
  revenueLift: "+8,2%",
  utilizationLift: "+5,1%",
  rejectedShortTrips: "-13%",
  note: "Doanh thu tăng nhưng vẫn giữ được room bán cho ga trung gian và giảm sold-out giả.",
};

export const simulationTable = [
  { metric: "Doanh thu", current: "2,41 tỷ", ai: "2,61 tỷ" },
  { metric: "Hệ số lấp đầy", current: "74%", ai: "79%" },
  { metric: "Vé ga trung gian", current: "1.840", ai: "2.110" },
  { metric: "Lượt tìm sold-out", current: "420", ai: "301" },
];

export const scenarioChart = [
  { name: "Hiện tại", revenue: 72, volume: 64 },
  { name: "AI đề xuất", revenue: 84, volume: 71 },
  { name: "AI + quota trung gian", revenue: 79, volume: 76 },
];

export const alerts = [
  {
    severity: "Cao",
    title: "Chặng Huế → Đà Nẵng sắp cháy vé",
    detail: "Tồn kho còn 6 ghế trong 18 giờ tới. Dự báo nhu cầu vượt năng lực 24%.",
  },
  {
    severity: "Trung bình",
    title: "Đoạn Nha Trang → Sài Gòn trống cao",
    detail: "Tồn kho dư 41 ghế, tốc độ booking thấp hơn dự báo 17%.",
  },
  {
    severity: "Cao",
    title: "Quota ga trung gian đang thấp",
    detail: "Vinh → Đồng Hới bị chặn bởi quota chặng dài ở 3 toa liên tiếp.",
  },
];

export const auditLogs = [
  {
    actor: "thu.nga",
    action: "Phê duyệt chính sách",
    entity: "price_policy: july-weekend",
    time: "17/07 16:35",
    before: "{ discount_cap: 0.12, quota_mid_stop: 0.18 }",
    after: "{ discount_cap: 0.08, quota_mid_stop: 0.22 }",
  },
  {
    actor: "ops.hoa",
    action: "Khóa cụm ghế",
    entity: "toa B2 ghế 13-18",
    time: "17/07 15:10",
    before: "{ status: available }",
    after: "{ status: reserved_operational }",
  },
  {
    actor: "it.phong",
    action: "Rollback chính sách",
    entity: "pricing_run: 2026-07-17T09:00",
    time: "17/07 13:42",
    before: "{ active: true }",
    after: "{ active: false }",
  },
];

export const trainCoaches = [
  {
    name: "Toa A1",
    type: "Ngồi mềm",
    occupancy: "76%",
    seats: ["A01", "A02", "A03", "A04", "A05", "A06", "A07", "A08", "A09", "A10", "A11", "A12"],
  },
  {
    name: "Toa B2",
    type: "Giường nằm K6",
    occupancy: "92%",
    seats: ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B09", "B10", "B11", "B12"],
  },
  {
    name: "Toa C3",
    type: "Giường nằm K6",
    occupancy: "64%",
    seats: ["C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C09", "C10", "C11", "C12"],
  },
];

export const selectedCoach = {
  route: "SE3 · 19/07/2026",
  coach: "Toa B2",
  seatLegend: [
    { tone: "available", label: "Còn trống" },
    { tone: "selected", label: "Đang chọn" },
    { tone: "held", label: "Đang giữ chỗ" },
    { tone: "blocked", label: "Khóa vận hành" },
  ],
  seats: [
    ["held", "held", "available", "available"],
    ["blocked", "selected", "available", "held"],
    ["available", "available", "available", "blocked"],
    ["held", "available", "selected", "available"],
  ],
};

export const rightRailCards = {
  quickAlerts: [
    {
      severity: "Cao",
      title: "Huế → Đà Nẵng tăng tải đột biến",
      body: "Tăng thêm 6% trong 2 giờ gần nhất, khả năng sold-out giả rất cao.",
    },
    {
      severity: "Trung bình",
      title: "Quota ngắn hạn vừa được mở",
      body: "Đã nhả thêm 12 chỗ cho luồng Vinh → Huế ở toa B2.",
    },
  ],
  savedViews: [
    {
      title: "Ga trung gian cuối tuần",
      meta: "Áp dụng cho nhóm tàu SE chạy thứ Sáu đến Chủ nhật",
    },
    {
      title: "Chặng cần mở bán thêm",
      meta: "03 route đang dư năng lực nhưng tốc độ bán thấp",
    },
  ],
  simulationStatus: {
    value: "41 / 60 lượt",
    body: "Nhóm đã dùng 68% hạn mức mô phỏng trong tháng này.",
  },
  updateStatus: {
    title: "Dữ liệu vừa cập nhật",
    body: "Đồng bộ giá, quota và tồn ghế lần cuối lúc 16:55, chậm 5 phút so với realtime.",
  },
};
