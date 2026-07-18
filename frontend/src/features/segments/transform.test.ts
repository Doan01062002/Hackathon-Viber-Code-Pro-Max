import { describe, expect, it } from "vitest";

import { buildSegmentHeatmap, legLoad, seatTypeLabel } from "./transform";
import type { LegHeatmapItemDto } from "./types";

function leg(partial: Partial<LegHeatmapItemDto>): LegHeatmapItemDto {
  return {
    segment_id: 1,
    sequence_no: 1,
    origin_station_code: "HAN",
    destination_station_code: "PHL",
    capacity: 100,
    remaining: 40,
    seat_type: "ngoi_mem",
    bid_price: 0,
    is_bottleneck: false,
    ...partial,
  };
}

describe("legLoad", () => {
  it("tải = (sức chứa - tồn) / sức chứa * 100", () => {
    expect(legLoad(leg({ capacity: 100, remaining: 40 }))).toBe(60);
  });

  it("trả 0 khi sức chứa = 0 (tránh chia cho 0)", () => {
    expect(legLoad(leg({ capacity: 0, remaining: 0 }))).toBe(0);
  });
});

describe("seatTypeLabel", () => {
  it("map mã backend sang nhãn tiếng Việt", () => {
    expect(seatTypeLabel("giuong_nam_k6")).toBe("Giường nằm K6");
    expect(seatTypeLabel("ngoi_mem")).toBe("Ngồi mềm");
  });

  it("giữ nguyên mã lạ không có trong bảng", () => {
    expect(seatTypeLabel("vip_cabin")).toBe("vip_cabin");
  });
});

describe("buildSegmentHeatmap", () => {
  it("trả null khi không có leg nào", () => {
    expect(buildSegmentHeatmap([])).toBeNull();
  });

  it("gom legs thành lưới chặng × loại chỗ", () => {
    const heatmap = buildSegmentHeatmap([
      leg({ sequence_no: 1, seat_type: "giuong_nam_k6", capacity: 100, remaining: 50 }),
      leg({ sequence_no: 1, seat_type: "ngoi_mem", capacity: 100, remaining: 20 }),
      leg({
        sequence_no: 2,
        origin_station_code: "PHL",
        destination_station_code: "NDI",
        seat_type: "giuong_nam_k6",
        capacity: 100,
        remaining: 90,
      }),
    ]);

    expect(heatmap!.columns.map((c) => c.key)).toEqual(["giuong_nam_k6", "ngoi_mem"]);
    expect(heatmap!.rows).toHaveLength(2);

    const seg1 = heatmap!.rows[0];
    expect(seg1.label).toBe("HAN → PHL");
    expect(seg1.loads.giuong_nam_k6).toBe(50);
    expect(seg1.loads.ngoi_mem).toBe(80);
  });

  it("để null cho ô loại chỗ không có dữ liệu", () => {
    const heatmap = buildSegmentHeatmap([
      leg({ sequence_no: 1, seat_type: "giuong_nam_k6" }),
      leg({ sequence_no: 2, seat_type: "ngoi_mem" }),
    ]);
    // seq 1 không có ngoi_mem → null; seq 2 không có giuong_nam_k6 → null.
    expect(heatmap!.rows[0].loads.ngoi_mem).toBeNull();
    expect(heatmap!.rows[1].loads.giuong_nam_k6).toBeNull();
  });

  it("đánh dấu nút cổ chai nếu bất kỳ leg nào của chặng is_bottleneck", () => {
    const heatmap = buildSegmentHeatmap([
      leg({ sequence_no: 1, seat_type: "giuong_nam_k6", is_bottleneck: false }),
      leg({ sequence_no: 1, seat_type: "ngoi_mem", is_bottleneck: true }),
    ]);
    expect(heatmap!.rows[0].isBottleneck).toBe(true);
  });

  it("sắp xếp hàng theo sequence_no tăng dần", () => {
    const heatmap = buildSegmentHeatmap([
      leg({ sequence_no: 3 }),
      leg({ sequence_no: 1 }),
      leg({ sequence_no: 2 }),
    ]);
    expect(heatmap!.rows.map((r) => r.seq)).toEqual([1, 2, 3]);
  });
});
