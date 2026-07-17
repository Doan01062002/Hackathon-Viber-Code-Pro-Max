/** Interface công khai của feature segments (Khối 1 - Dự báo: tải chặng). */
export { useSegmentsLoad } from "./hooks/useSegmentsLoad";
export { buildSegmentHeatmap, legLoad, seatTypeLabel } from "./transform";
export type { SegmentHeatmap, SegmentColumn, SegmentHeatRow } from "./transform";
export type { LegHeatmapItemDto, LegHeatmapResponseDto } from "./types";
