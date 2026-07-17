/** Biến đổi legs của backend thành lưới heatmap tải chặng. */

import type { LegHeatmapItemDto } from "./types";

/** Nhãn thân thiện cho mã loại chỗ của backend. */
const SEAT_TYPE_LABELS: Record<string, string> = {
  giuong_nam_k6: "Giường nằm K6",
  ngoi_mem: "Ngồi mềm",
};

export function seatTypeLabel(code: string): string {
  return SEAT_TYPE_LABELS[code] ?? code;
}

export type SegmentColumn = { key: string; label: string };

export type SegmentHeatRow = {
  seq: number;
  label: string;
  isBottleneck: boolean;
  loads: Record<string, number | null>;
};

export type SegmentHeatmap = {
  columns: SegmentColumn[];
  rows: SegmentHeatRow[];
};

/** Tỉ lệ lấp đầy của một chặng = (sức chứa - tồn) / sức chứa, theo %. */
export function legLoad(leg: LegHeatmapItemDto): number {
  if (!leg.capacity) return 0;
  return ((leg.capacity - leg.remaining) / leg.capacity) * 100;
}

/**
 * Backend legs-heatmap không có chiều thời gian; mỗi chặng có tải theo *loại chỗ*.
 * Gom legs thành lưới: hàng = chặng (theo sequence_no), cột = loại chỗ.
 */
export function buildSegmentHeatmap(legs: LegHeatmapItemDto[]): SegmentHeatmap | null {
  if (legs.length === 0) return null;

  const columnKeys: string[] = [];
  for (const leg of legs) {
    if (!columnKeys.includes(leg.seat_type)) columnKeys.push(leg.seat_type);
  }
  const columns = columnKeys.map((key) => ({ key, label: seatTypeLabel(key) }));

  const rowsBySeq = new Map<number, SegmentHeatRow>();
  for (const leg of [...legs].sort((a, b) => a.sequence_no - b.sequence_no)) {
    let row = rowsBySeq.get(leg.sequence_no);
    if (!row) {
      row = {
        seq: leg.sequence_no,
        label: `${leg.origin_station_code} → ${leg.destination_station_code}`,
        isBottleneck: false,
        loads: Object.fromEntries(columnKeys.map((key) => [key, null])),
      };
      rowsBySeq.set(leg.sequence_no, row);
    }
    row.loads[leg.seat_type] = legLoad(leg);
    if (leg.is_bottleneck) row.isBottleneck = true;
  }

  return { columns, rows: [...rowsBySeq.values()] };
}
