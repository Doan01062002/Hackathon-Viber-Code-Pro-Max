import type { StationOption } from "@/components/ui/SearchableStationSelect";

export const STATION_OPTIONS: StationOption[] = [
  { code: "HAN", name: "Hà Nội", region: "Hà Nội" },
  { code: "PHL", name: "Phủ Lý", region: "Hà Nam" },
  { code: "NDI", name: "Nam Định", region: "Nam Định" },
  { code: "NBH", name: "Ninh Bình", region: "Ninh Bình" },
  { code: "THH", name: "Thanh Hóa", region: "Thanh Hóa" },
  { code: "VIH", name: "Vinh", region: "Nghệ An" },
  { code: "DHO", name: "Đồng Hới", region: "Quảng Bình" },
  { code: "DHA", name: "Đông Hà", region: "Quảng Trị" },
  { code: "HUE", name: "Huế", region: "Thừa Thiên Huế" },
  { code: "DAN", name: "Đà Nẵng", region: "Đà Nẵng" },
  { code: "TAK", name: "Tam Kỳ", region: "Quảng Nam" },
  { code: "QNG", name: "Quảng Ngãi", region: "Quảng Ngãi" },
  { code: "DTR", name: "Diêu Trì (Quy Nhơn)", region: "Bình Định" },
  { code: "TYH", name: "Tuy Hòa", region: "Phú Yên" },
  { code: "NTG", name: "Nha Trang", region: "Khánh Hòa" },
  { code: "TPC", name: "Tháp Chàm", region: "Ninh Thuận" },
  { code: "BTH", name: "Bình Thuận (Mương Mán)", region: "Bình Thuận" },
  { code: "LKH", name: "Long Khánh", region: "Đồng Nai" },
  { code: "BHO", name: "Biên Hòa", region: "Đồng Nai" },
  { code: "SGO", name: "Sài Gòn", region: "TP. Hồ Chí Minh" },
];

export function getStationLabel(code: string): string {
  const station = STATION_OPTIONS.find((item) => item.code === code);
  return station ? station.name : code;
}

export function toStationOptions(
  stations: Array<{ code: string; name: string }>,
): StationOption[] {
  return stations.map((station) => {
    const matched = STATION_OPTIONS.find((item) => item.code === station.code);
    return {
      code: station.code,
      name: matched ? matched.name : station.name,
      region: matched ? matched.region : "",
    };
  });
}
