/** Định dạng dùng chung cho các màn hình vé. */

const money = new Intl.NumberFormat("vi-VN", {
  style: "currency",
  currency: "VND",
  maximumFractionDigits: 0,
});

const clock = new Intl.DateTimeFormat("vi-VN", {
  hour: "2-digit",
  minute: "2-digit",
  timeZone: "Asia/Ho_Chi_Minh",
});

const dayMonth = new Intl.DateTimeFormat("vi-VN", {
  day: "2-digit",
  month: "2-digit",
  timeZone: "Asia/Ho_Chi_Minh",
});

export function formatMoney(value: number): string {
  return money.format(value);
}

/** "19:30" theo giờ Việt Nam. */
export function formatClock(isoValue: string): string {
  return clock.format(new Date(isoValue));
}

/** "19:30 - 21:45" cho một chặng; thêm ngày nếu chặng qua đêm. */
export function formatLegWindow(departureAt: string, arrivalAt: string): string {
  const departure = new Date(departureAt);
  const arrival = new Date(arrivalAt);
  const crossesDay = dayMonth.format(departure) !== dayMonth.format(arrival);
  const arrivalLabel = crossesDay
    ? `${clock.format(arrival)} (${dayMonth.format(arrival)})`
    : clock.format(arrival);
  return `${clock.format(departure)} - ${arrivalLabel}`;
}
