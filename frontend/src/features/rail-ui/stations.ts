import type { StationOption } from "@/components/ui/SearchableStationSelect";

export const STATION_OPTIONS: StationOption[] = [
  { code: "HAN", name: "Ha Noi", region: "Ha Noi" },
  { code: "PHL", name: "Phu Ly", region: "Ha Nam" },
  { code: "NDI", name: "Nam Dinh", region: "Nam Dinh" },
  { code: "NBH", name: "Ninh Binh", region: "Ninh Binh" },
  { code: "THH", name: "Thanh Hoa", region: "Thanh Hoa" },
  { code: "VIH", name: "Vinh", region: "Nghe An" },
  { code: "DHO", name: "Dong Hoi", region: "Quang Binh" },
  { code: "DHA", name: "Dong Ha", region: "Quang Tri" },
  { code: "HUE", name: "Hue", region: "Thua Thien Hue" },
  { code: "DAN", name: "Da Nang", region: "Da Nang" },
  { code: "TAK", name: "Tam Ky", region: "Quang Nam" },
  { code: "QNG", name: "Quang Ngai", region: "Quang Ngai" },
  { code: "DTR", name: "Dieu Tri (Quy Nhon)", region: "Binh Dinh" },
  { code: "TYH", name: "Tuy Hoa", region: "Phu Yen" },
  { code: "NTG", name: "Nha Trang", region: "Khanh Hoa" },
  { code: "TPC", name: "Thap Cham", region: "Ninh Thuan" },
  { code: "BTH", name: "Binh Thuan (Muong Man)", region: "Binh Thuan" },
  { code: "LKH", name: "Long Khanh", region: "Dong Nai" },
  { code: "BHO", name: "Bien Hoa", region: "Dong Nai" },
  { code: "SGO", name: "Sai Gon", region: "TP. Ho Chi Minh" },
];

export function getStationLabel(code: string): string {
  const station = STATION_OPTIONS.find((item) => item.code === code);
  return station ? station.name : code;
}

export function toStationOptions(
  stations: Array<{ code: string; name: string }>,
): StationOption[] {
  return stations.map((station) => ({ code: station.code, name: station.name }));
}
