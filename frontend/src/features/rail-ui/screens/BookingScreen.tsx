"use client";

import Link from "next/link";
import { useEffect, useState, useRef } from "react";
import { Button } from "@/components/ui/Button";
import { SearchableStationSelect } from "@/components/ui/SearchableStationSelect";
import {
  confirmBooking,
  createBookingHold,
  getBookingOptions,
  getBookingSeatPlan,
  searchBookingProducts,
} from "@/features/booking/api/bookingApi";
import type {
  BookingConfirmResponse,
  BookingOptions,
  BookingSearchItem,
  BookingSeat,
  BookingSeatPlan,
} from "@/features/booking/types";
import { useRailCatalog } from "@/features/catalog/hooks/useRailCatalog";
import { createPricingQuote } from "@/features/quote/api/quoteApi";
import { RouteMap, type RouteSegment } from "@/features/rail-ui/components/RouteMap";
import { STATION_OPTIONS, toStationOptions } from "@/features/rail-ui/stations";
import { ApiError } from "@/lib/api/client";

const FALLBACK_DATE = "2025-12-30";

const moneyFormatter = new Intl.NumberFormat("vi-VN", {
  style: "currency",
  currency: "VND",
  maximumFractionDigits: 0,
});

function chunkSeats(seats: BookingSeat[], size: number): BookingSeat[][] {
  const chunks: BookingSeat[][] = [];
  for (let index = 0; index < seats.length; index += size) {
    chunks.push(seats.slice(index, index + size));
  }
  return chunks;
}

function formatTime(value: string): string {
  return new Intl.DateTimeFormat("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    day: "2-digit",
    month: "2-digit",
  }).format(new Date(value));
}

/**
 * Ghế người dùng đang chọn. Lưu kèm toa và sản phẩm OD vì giỏ chọn có thể
 * trải trên nhiều toa với loại chỗ (và giá) khác nhau.
 */
type PickedSeat = {
  seatId: number;
  seatNo: string;
  coachNo: string;
  odProductId: number;
  tripId: number;
  seatType: string;
  basePrice: number;
};

export function BookingScreen() {
  const { catalog, error: catalogError } = useRailCatalog();
  const allStations = catalog ? toStationOptions(catalog.stations) : STATION_OPTIONS;

  const [origin, setOrigin] = useState("HAN");
  const [destination, setDestination] = useState("HUE");
  const [departureDate, setDepartureDate] = useState(FALLBACK_DATE);
  const [returnDate, setReturnDate] = useState("");
  const [bookingOptions, setBookingOptions] = useState<BookingOptions | null>(null);
  const [products, setProducts] = useState<BookingSearchItem[]>([]);
  const [returnProducts, setReturnProducts] = useState<BookingSearchItem[]>([]);
  const [selectedTripId, setSelectedTripId] = useState<number | null>(null);
  const [plans, setPlans] = useState<Record<number, BookingSeatPlan>>({});
  const [selectedCoachNo, setSelectedCoachNo] = useState("");
  const [pickedSeats, setPickedSeats] = useState<PickedSeat[]>([]);
  const [refreshVersion, setRefreshVersion] = useState(0);

  const [loadingOptions, setLoadingOptions] = useState(false);
  const [loadingProducts, setLoadingProducts] = useState(false);
  const [loadingPlans, setLoadingPlans] = useState(false);
  const [booking, setBooking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmed, setConfirmed] = useState<BookingConfirmResponse[]>([]);
  const [paidPrice, setPaidPrice] = useState(0);

  // States for interactive combined seat selection (FR2.7 / PM requirement)
  const [isCombinedMode, setIsCombinedMode] = useState(false);
  const [combinedLegs, setCombinedLegs] = useState<{ leg: string; seatNo: string; coachNo: string; seatId: number; time: string; note?: string }[]>([]);

  useEffect(() => {
    const controller = new AbortController();
    const loadOptions = () => {
      setLoadingOptions(true);
      return getBookingOptions(origin, destination, controller.signal)
        .then((result) => {
          setBookingOptions(result);
          const destinationExists = result.destinations.some((item) => item.code === destination);
          if (!destinationExists && result.destinations[0]) {
            setDestination(result.destinations[0].code);
            return;
          }
          if (result.departure_dates.length > 0 && !result.departure_dates.includes(departureDate)) {
            setDepartureDate(result.departure_dates.at(-1) ?? FALLBACK_DATE);
          }
          if (returnDate && !result.return_dates.includes(returnDate)) {
            setReturnDate("");
          }
        })
        .catch((caught: unknown) => {
          if (!(caught instanceof DOMException && caught.name === "AbortError")) {
            setError(caught instanceof Error ? caught.message : "Khong tai duoc lua chon hanh trinh");
          }
        })
        .finally(() => setLoadingOptions(false));
    };
    void loadOptions();
    // Tam ngung tu dong cap nhat DB
    // const interval = window.setInterval(loadOptions, 60_000);
    // const handleFocus = () => void loadOptions();
    // window.addEventListener("focus", handleFocus);
    return () => {
      controller.abort();
      // window.clearInterval(interval);
      // window.removeEventListener("focus", handleFocus);
    };
  }, [departureDate, destination, origin, returnDate]);

  useEffect(() => {
    if (!origin || !destination || !departureDate) return;
    const controller = new AbortController();
    const loadProducts = () => {
      setLoadingProducts(true);
      setError(null);
      return searchBookingProducts(origin, destination, departureDate, controller.signal)
        .then((result) => {
          setProducts(result);
          setSelectedTripId((current) =>
            current && result.some((item) => item.trip_id === current)
              ? current
              : (result[0]?.trip_id ?? null),
          );
        })
        .catch((caught: unknown) => {
          if (!(caught instanceof DOMException && caught.name === "AbortError")) {
            setError(caught instanceof Error ? caught.message : "Khong tim duoc chuyen tau");
            setProducts([]);
          }
        })
        .finally(() => setLoadingProducts(false));
    };
    setConfirmed([]);
    setPickedSeats([]);
    void loadProducts();
    // Tam ngung tu dong cap nhat DB
    // const interval = window.setInterval(loadProducts, 30_000);
    // const handleFocus = () => void loadProducts();
    // window.addEventListener("focus", handleFocus);
    return () => {
      controller.abort();
      // window.clearInterval(interval);
      // window.removeEventListener("focus", handleFocus);
    };
  }, [departureDate, destination, origin]);

  useEffect(() => {
    if (!returnDate) {
      setReturnProducts([]);
      return;
    }
    const controller = new AbortController();
    searchBookingProducts(destination, origin, returnDate, controller.signal)
      .then(setReturnProducts)
      .catch(() => setReturnProducts([]));
    return () => controller.abort();
  }, [destination, origin, returnDate]);

  // Đổi chuyến thì giỏ ghế của chuyến cũ không còn ý nghĩa.
  useEffect(() => {
    setPickedSeats([]);
  }, [selectedTripId]);

  useEffect(() => {
    const tripProducts = products.filter((item) => item.trip_id === selectedTripId);
    if (tripProducts.length === 0) {
      setPlans({});
      setSelectedCoachNo("");
      return;
    }

    let active = true;
    const loadPlans = async () => {
      setLoadingPlans(true);
      try {
        const loaded = await Promise.all(
          tripProducts.map((product) => getBookingSeatPlan(product.od_product_id)),
        );
        if (!active) return;
        const nextPlans = Object.fromEntries(loaded.map((plan) => [plan.od_product_id, plan]));
        setPlans(nextPlans);
        const coachNumbers = loaded
          .flatMap((plan) => plan.coaches.map((coach) => coach.coach_no))
          .sort((left, right) => left.localeCompare(right));
        setSelectedCoachNo((current) =>
          coachNumbers.includes(current) ? current : (coachNumbers[0] ?? ""),
        );
      } catch (caught) {
        if (active) setError(caught instanceof Error ? caught.message : "Khong tai duoc so do tau");
      } finally {
        if (active) setLoadingPlans(false);
      }
    };

    void loadPlans();
    // Tam ngung tu dong cap nhat DB
    // const interval = window.setInterval(loadPlans, 10_000);
    // const handleFocus = () => void loadPlans();
    // window.addEventListener("focus", handleFocus);
    return () => {
      active = false;
      // window.clearInterval(interval);
      // window.removeEventListener("focus", handleFocus);
    };
  }, [refreshVersion, selectedTripId, products]);

  const selectedTripProducts = products.filter((item) => item.trip_id === selectedTripId);

  const triggerCombinedMode = () => {
    setIsCombinedMode(true);
    setPickedSeats([]);
    // Setup mock combined legs (4 segments for high-granularity visual demo)
    setCombinedLegs([
      {
        leg: "Hà Nội → Thanh Hóa",
        seatNo: "Ghế 12",
        coachNo: "01",
        seatId: 101,
        time: "19:30 - 21:45",
      },
      {
        leg: "Thanh Hóa → Vinh",
        seatNo: "Ghế 08",
        coachNo: "02",
        seatId: 102,
        time: "21:55 - 00:15",
        note: "Đổi từ Toa 01 Ghế 12 sang Toa 02 Ghế 08 tại Thanh Hóa (dừng 10 phút).",
      },
      {
        leg: "Vinh → Đà Nẵng",
        seatNo: "Ghế 15",
        coachNo: "02",
        seatId: 103,
        time: "00:25 - 06:10",
        note: "Di chuyển sang Ghế 15 cùng Toa 02 tại ga Vinh (dừng 10 phút).",
      },
      {
        leg: "Đà Nẵng → Sài Gòn",
        seatNo: "Ghế 24",
        coachNo: "03",
        seatId: 104,
        time: "06:20 - 18:45",
        note: "Đổi sang Toa 03 Ghế 24 tại ga Đà Nẵng (dừng 10 phút).",
      }
    ]);
  };

  const coachEntries = selectedTripProducts
    .flatMap((product) =>
      (plans[product.od_product_id]?.coaches ?? []).map((coach) => ({ product, coach })),
    )
    .sort((left, right) => left.coach.coach_no.localeCompare(right.coach.coach_no));
  const selectedCoachEntry = coachEntries.find((entry) => entry.coach.coach_no === selectedCoachNo);
  const selectedProduct = selectedCoachEntry?.product ?? null;
  const selectedPlan = selectedProduct ? plans[selectedProduct.od_product_id] : null;
  const selectedSeats = selectedCoachEntry?.coach.seats ?? [];
  const isSleeper = selectedCoachEntry?.coach.seat_type === "giuong_nam_k6";
  const tripChoices = Array.from(new Map(products.map((item) => [item.trip_id, item])).values());

  const destinationStations = bookingOptions
    ? bookingOptions.destinations.map((item) => ({ code: item.code, name: item.name }))
    : allStations.filter((station) => station.code !== origin);

  const routeSegments: RouteSegment[] = (selectedPlan?.segments ?? []).map((segment) => ({
    id: String(segment.segment_id),
    label: `${segment.origin_name} - ${segment.destination_name}`,
    loadPct: segment.load_pct,
    originCode: segment.origin_code,
    originName: segment.origin_name,
    destinationCode: segment.destination_code,
    destinationName: segment.destination_name,
    remaining: segment.remaining,
    capacity: segment.capacity,
  }));

  const pickedSeatIds = new Set(pickedSeats.map((item) => item.seatId));
  const estimatedTotal = pickedSeats.reduce((total, item) => total + item.basePrice, 0);

  function selectCoach(coachNo: string) {
    setSelectedCoachNo(coachNo);
    // Không xoá `pickedSeats` lẫn `confirmed`: giỏ ghế đang chọn và vé đã đặt
    // thuộc về cả phiên làm việc, không phải của riêng toa đang xem.
  }

  function toggleSeat(seat: BookingSeat) {
    if (seat.status !== "available" || !selectedProduct || !selectedCoachEntry) return;
    setPickedSeats((current) =>
      current.some((item) => item.seatId === seat.seat_id)
        ? current.filter((item) => item.seatId !== seat.seat_id)
        : [
            ...current,
            {
              seatId: seat.seat_id,
              seatNo: seat.seat_no,
              coachNo: selectedCoachEntry.coach.coach_no,
              odProductId: selectedProduct.od_product_id,
              tripId: selectedProduct.trip_id,
              seatType: selectedProduct.seat_type,
              basePrice: selectedProduct.base_price,
            },
          ],
    );
  }

  async function handleConfirm() {
    if (pickedSeats.length === 0 || booking) return;
    setBooking(true);
    setError(null);
    try {
      // Ghế có thể trải trên nhiều sản phẩm OD (loại chỗ khác nhau ⇒ giá khác
      // nhau), nên phải lấy quote riêng cho từng nhóm.
      const groups = new Map<number, PickedSeat[]>();
      for (const item of pickedSeats) {
        groups.set(item.odProductId, [...(groups.get(item.odProductId) ?? []), item]);
      }

      const results: BookingConfirmResponse[] = [];
      let total = 0;
      for (const group of groups.values()) {
        const quote = await createPricingQuote({
          origin,
          destination,
          service_date: departureDate,
          seat_type: group[0].seatType,
          trip_id: group[0].tripId,
        });
        for (const item of group) {
          const hold = await createBookingHold({
            od_product_id: quote.od_product_id,
            seat_id: item.seatId,
            quote_id: quote.quote_id,
            channel: "web",
          });
          results.push(await confirmBooking(hold.booking_id));
        }
        total += quote.final_price * group.length;
      }
      // Cộng dồn để không mất vé của các lần đặt trước trong cùng phiên.
      setConfirmed((current) => [...current, ...results]);
      setPaidPrice((current) => current + total);
      setPickedSeats([]);
      setRefreshVersion((value) => value + 1);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Dat ve that bai, vui long thu lai");
      setRefreshVersion((value) => value + 1);
    } finally {
      setBooking(false);
    }
  }

  return (
    <div className="space-y-6">
      {catalogError || error ? (
        <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded-lg text-yellow-800 text-xs font-semibold">
          {error ?? catalogError}
        </div>
      ) : null}

      <div className="grid grid-cols-12 gap-6">
        <section className="col-span-12 lg:col-span-8 space-y-6">
          <div className="bg-white border border-outline-variant rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between gap-3 mb-4">
              <h3 className="font-bold text-sm text-on-surface flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-sm">train</span>
                Sơ đồ đoàn tàu {selectedPlan ? `· ${selectedPlan.train_code}` : ""}
              </h3>
              {loadingPlans ? <span className="text-[10px] font-bold text-primary animate-pulse">Đang cập nhật...</span> : null}
            </div>

            {coachEntries.length > 0 ? (
              <div className="flex gap-2 overflow-x-auto custom-scrollbar pb-3 pt-1">
                <div className="w-24 h-[70px] shrink-0 bg-slate-50 border border-slate-200 rounded-lg flex flex-col items-center justify-center gap-1 p-2 select-none text-slate-400">
                  <span className="w-full text-center text-[10px] font-black uppercase tracking-wider leading-none">Đầu tàu</span>
                  <div className="flex items-center justify-center">
                    <span className="material-symbols-outlined text-xl leading-none">train</span>
                  </div>
                </div>
                {coachEntries.map(({ product, coach }) => {
                  const selected = coach.coach_no === selectedCoachNo;
                  const sleeper = coach.seat_type === "giuong_nam_k6";
                  const isFull = coach.available_seats === 0;
                  return (
                    <button
                      key={`${product.od_product_id}-${coach.coach_no}`}
                      type="button"
                      onClick={() => selectCoach(coach.coach_no)}
                      className={`w-24 h-[70px] shrink-0 rounded-lg border p-2 flex flex-col items-center justify-center gap-1.5 transition-all ${
                        selected
                          ? "border-primary ring-1 ring-primary bg-primary/5 text-primary"
                          : isFull
                          ? "border-slate-200 bg-slate-100/60 text-slate-400 hover:border-slate-300"
                          : "border-outline-variant hover:border-primary/50 text-slate-700 bg-white"
                      }`}
                    >
                      <span className={`w-full text-center text-[10px] font-black leading-none ${
                        selected ? "text-primary" : isFull ? "text-slate-400" : "text-slate-800"
                      }`}>
                        Toa {coach.coach_no}
                      </span>
                      <div className="flex items-center justify-center gap-1 w-full">
                        <span className="material-symbols-outlined text-lg leading-none shrink-0">
                          {sleeper ? "hotel" : "chair"}
                        </span>
                        <span className="whitespace-nowrap text-[10px] font-black font-mono leading-none">
                          {coach.total_seats - coach.available_seats}/{coach.total_seats}
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            ) : (
              <div className="h-20 rounded-lg border border-dashed border-outline-variant flex items-center justify-center text-xs font-semibold text-on-surface-variant">
                {loadingProducts || loadingPlans ? "Đang tải cấu hình đoàn tàu..." : "Không có đoàn tàu phù hợp."}
              </div>
            )}
          </div>

          <div className="bg-white border border-outline-variant rounded-xl p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
              <h3 className="font-bold text-sm text-on-surface flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-sm">airline_seat_recline_normal</span>
                Toa {selectedCoachNo || "--"} · {isSleeper ? "Giường nằm khoang 6" : "Ngồi mềm điều hòa"}
              </h3>
              <div className="flex gap-3 text-[9px] font-bold">
                <span className="flex items-center gap-1"><i className="w-3 h-3 rounded border bg-white" />Còn trống</span>
                <span className="flex items-center gap-1"><i className="w-3 h-3 rounded bg-slate-300" />Đã giữ/bán</span>
                <span className="flex items-center gap-1"><i className="w-3 h-3 rounded bg-primary" />Đang chọn</span>
              </div>
            </div>

            {isCombinedMode ? (
              /* 4-COACH Z-SHAPE COMBINED LAYOUT (PM/TEAMMATE Z-SHAPE PATHWAY SPECIFICATION) */
              <div className="space-y-6">
                <div className="grid grid-cols-[1fr_auto_1fr] gap-y-6 gap-x-4 items-center p-6 bg-slate-50 rounded-2xl border border-slate-200 max-w-4xl mx-auto">
                  
                  {/* ROW 1: Left to Right */}
                  {/* Toa 01 */}
                  <div className="bg-white border border-outline-variant/65 rounded-xl p-3 shadow-sm relative">
                    <div className="text-[10px] font-black text-purple-700 border-b border-purple-100 pb-1.5 text-center uppercase tracking-wider mb-2">
                      Toa 01 (Chặng 1: HAN → TH)
                    </div>
                    <div className="grid grid-cols-4 gap-1 bg-slate-50 p-2 rounded border text-center">
                      <div className="h-6 rounded bg-slate-300 text-slate-500 text-[8px] font-black flex items-center justify-center cursor-not-allowed">10</div>
                      <div className="h-6 rounded bg-slate-300 text-slate-500 text-[8px] font-black flex items-center justify-center cursor-not-allowed">11</div>
                      <div className="h-6 rounded bg-purple-600 text-white text-[8px] font-black flex items-center justify-center scale-105 shadow-sm ring-2 ring-purple-600 ring-offset-1 relative">
                        12
                      </div>
                      <div className="h-6 rounded bg-slate-300 text-slate-500 text-[8px] font-black flex items-center justify-center cursor-not-allowed">13</div>
                    </div>
                    <p className="text-[9px] text-on-surface-variant font-bold text-center mt-2">Ghế 12 • Ga đi: Hà Nội</p>
                  </div>

                  {/* Arrow 1: Right */}
                  <div className="flex flex-col items-center px-2 text-purple-600 text-center select-none">
                    <span className="material-symbols-outlined text-lg font-black animate-pulse">arrow_forward</span>
                    <span className="text-[7.5px] font-black uppercase tracking-wider mt-0.5 text-slate-500">Thanh Hóa</span>
                  </div>

                  {/* Toa 02 (Chặng 2) */}
                  <div className="bg-white border border-outline-variant/65 rounded-xl p-3 shadow-sm relative">
                    <div className="text-[10px] font-black text-blue-700 border-b border-blue-100 pb-1.5 text-center uppercase tracking-wider mb-2">
                      Toa 02 (Chặng 2: TH → VII)
                    </div>
                    <div className="grid grid-cols-4 gap-1 bg-slate-50 p-2 rounded border text-center">
                      <div className="h-6 rounded bg-slate-300 text-slate-500 text-[8px] font-black flex items-center justify-center cursor-not-allowed">6</div>
                      <div className="h-6 rounded bg-slate-300 text-slate-500 text-[8px] font-black flex items-center justify-center cursor-not-allowed">7</div>
                      <div className="h-6 rounded bg-blue-600 text-white text-[8px] font-black flex items-center justify-center scale-105 shadow-sm ring-2 ring-blue-600 ring-offset-1 relative">
                        08
                      </div>
                      <div className="h-6 rounded bg-slate-300 text-slate-500 text-[8px] font-black flex items-center justify-center cursor-not-allowed">9</div>
                    </div>
                    <p className="text-[9px] text-on-surface-variant font-bold text-center mt-2">Ghế 08 • Đổi toa/ghế</p>
                  </div>

                  {/* ROW 2: Diagonal Down-Left in the middle column */}
                  <div />
                  {/* Arrow 2: South West (Diagonal Down-Left ↙) */}
                  <div className="flex flex-col items-center py-1.5 text-blue-600 text-center select-none justify-self-center">
                    <span className="material-symbols-outlined text-lg font-black animate-pulse">south_west</span>
                    <span className="text-[7.5px] font-black uppercase tracking-wider mt-0.5 text-slate-500">Ga Vinh</span>
                  </div>
                  <div />

                  {/* ROW 3: Left to Right again (forming the Z shape) */}
                  {/* Toa 02 (Chặng 3) */}
                  <div className="bg-white border border-outline-variant/65 rounded-xl p-3 shadow-sm relative">
                    <div className="text-[10px] font-black text-amber-700 border-b border-amber-100 pb-1.5 text-center uppercase tracking-wider mb-2">
                      Toa 02 (Chặng 3: VII → DAD)
                    </div>
                    <div className="grid grid-cols-4 gap-1 bg-slate-50 p-2 rounded border text-center">
                      <div className="h-6 rounded bg-slate-300 text-slate-500 text-[8px] font-black flex items-center justify-center cursor-not-allowed">13</div>
                      <div className="h-6 rounded bg-slate-300 text-slate-500 text-[8px] font-black flex items-center justify-center cursor-not-allowed">14</div>
                      <div className="h-6 rounded bg-amber-500 text-white text-[8px] font-black flex items-center justify-center scale-105 shadow-sm ring-2 ring-amber-500 ring-offset-1 relative">
                        15
                      </div>
                      <div className="h-6 rounded bg-slate-300 text-slate-500 text-[8px] font-black flex items-center justify-center cursor-not-allowed">16</div>
                    </div>
                    <p className="text-[9px] text-on-surface-variant font-bold text-center mt-2">Ghế 15 • Đổi chỗ cùng toa</p>
                  </div>

                  {/* Arrow 3: Right */}
                  <div className="flex flex-col items-center px-2 text-amber-700 text-center select-none">
                    <span className="material-symbols-outlined text-lg font-black animate-pulse">arrow_forward</span>
                    <span className="text-[7.5px] font-black uppercase tracking-wider mt-0.5 text-slate-500">Đà Nẵng</span>
                  </div>

                  {/* Toa 03 */}
                  <div className="bg-white border border-outline-variant/65 rounded-xl p-3 shadow-sm relative">
                    <div className="text-[10px] font-black text-emerald-700 border-b border-emerald-100 pb-1.5 text-center uppercase tracking-wider mb-2">
                      Toa 03 (Chặng 4: DAD → SGN)
                    </div>
                    <div className="grid grid-cols-4 gap-1 bg-slate-50 p-2 rounded border text-center">
                      <div className="h-6 rounded bg-slate-300 text-slate-500 text-[8px] font-black flex items-center justify-center cursor-not-allowed">22</div>
                      <div className="h-6 rounded bg-slate-300 text-slate-500 text-[8px] font-black flex items-center justify-center cursor-not-allowed">23</div>
                      <div className="h-6 rounded bg-emerald-600 text-white text-[8px] font-black flex items-center justify-center scale-105 shadow-sm ring-2 ring-emerald-600 ring-offset-1 relative">
                        24
                      </div>
                      <div className="h-6 rounded bg-slate-300 text-slate-500 text-[8px] font-black flex items-center justify-center cursor-not-allowed">25</div>
                    </div>
                    <p className="text-[9px] text-on-surface-variant font-bold text-center mt-2">Ghế 24 • Ga cuối: Sài Gòn</p>
                  </div>

                </div>

                {/* Hybrid Segment Detail Table (Leg-by-Leg details) */}
                <div className="border border-outline-variant/65 rounded-xl overflow-hidden shadow-sm bg-white">
                  <div className="bg-slate-50 px-4 py-2 border-b border-outline-variant/45 flex justify-between items-center text-xs">
                    <span className="text-[10px] font-black uppercase text-slate-500 tracking-wider">Danh Sách Bảng Chi Tiết Chặng Ghép</span>
                    <span className="text-[9px] font-black bg-purple-100 text-purple-700 px-2 py-0.5 rounded">Tối ưu bởi AI</span>
                  </div>
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-50/20 text-[10px] uppercase font-bold text-slate-400 border-b border-outline-variant/20">
                        <th className="py-2.5 px-4 font-black">Chặng</th>
                        <th className="py-2.5 px-4 font-black">Phân đoạn hành trình</th>
                        <th className="py-2.5 px-4 font-black">Thời gian chạy</th>
                        <th className="py-2.5 px-4 font-black">Vị trí chỗ</th>
                        <th className="py-2.5 px-4 font-black">Chỉ dẫn AI</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-outline-variant/20 text-slate-700 font-semibold">
                      <tr className="hover:bg-slate-50/40">
                        <td className="py-2.5 px-4 text-purple-700 font-black">Chặng 1</td>
                        <td className="py-2.5 px-4">Hà Nội (HAN) → Thanh Hóa (THH)</td>
                        <td className="py-2.5 px-4 font-mono">19:30 - 21:45</td>
                        <td className="py-2.5 px-4">Toa 01 • <span className="text-purple-700 font-black">Ghế 12</span></td>
                        <td className="py-2.5 px-4 text-slate-400 font-medium">Bắt đầu hành trình tại Ga Hà Nội</td>
                      </tr>
                      <tr className="hover:bg-slate-50/40">
                        <td className="py-2.5 px-4 text-blue-700 font-black">Chặng 2</td>
                        <td className="py-2.5 px-4">Thanh Hóa (THH) → Vinh (VII)</td>
                        <td className="py-2.5 px-4 font-mono">21:55 - 00:15</td>
                        <td className="py-2.5 px-4 text-blue-700">Toa 02 • <span className="text-blue-700 font-black">Ghế 08</span></td>
                        <td className="py-2.5 px-4 text-blue-700 font-bold italic">
                          Đổi từ Toa 01 Ghế 12 sang Toa 02 Ghế 08 tại Thanh Hóa (dừng 10 phút).
                        </td>
                      </tr>
                      <tr className="hover:bg-slate-50/40">
                        <td className="py-2.5 px-4 text-amber-700 font-black">Chặng 3</td>
                        <td className="py-2.5 px-4">Vinh (VII) → Đà Nẵng (DAD)</td>
                        <td className="py-2.5 px-4 font-mono">00:25 - 06:10</td>
                        <td className="py-2.5 px-4 text-amber-700">Toa 02 • <span className="text-amber-700 font-black">Ghế 15</span></td>
                        <td className="py-2.5 px-4 text-amber-700 font-bold italic">
                          Đổi sang Ghế 15 cùng Toa 02 tại ga Vinh (dừng 10 phút).
                        </td>
                      </tr>
                      <tr className="hover:bg-slate-50/40">
                        <td className="py-2.5 px-4 text-emerald-700 font-black">Chặng 4</td>
                        <td className="py-2.5 px-4">Đà Nẵng (DAD) → Sài Gòn (SGN)</td>
                        <td className="py-2.5 px-4 font-mono">06:20 - 18:45</td>
                        <td className="py-2.5 px-4 text-emerald-700">Toa 03 • <span className="text-emerald-700 font-black">Ghế 24</span></td>
                        <td className="py-2.5 px-4 text-emerald-700 font-bold italic">
                          Đổi sang Toa 03 Ghế 24 tại ga Đà Nẵng (dừng 10 phút).
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            ) : selectedSeats.length > 0 ? (
              <div className="max-h-[430px] overflow-auto custom-scrollbar rounded-2xl border-2 border-slate-300 bg-slate-50 p-4">
                {isSleeper ? (
                  <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-3">
                    {chunkSeats(selectedSeats, 6).map((compartment, index) => (
                      <div key={index} className="rounded-xl border bg-white p-3">
                        <p className="text-[9px] font-black uppercase text-on-surface-variant mb-2">Khoang {index + 1}</p>
                        <div className="grid grid-cols-2 gap-2">
                          {compartment.map((seat, seatIndex) => (
                            <SeatButton key={seat.seat_id} seat={seat} selected={pickedSeatIds.has(seat.seat_id)} onClick={toggleSeat} suffix={`T${Math.floor(seatIndex / 2) + 1}`} />
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  (() => {
                    const seatRows = chunkSeats(selectedSeats, 4);
                    return (
                      <div className="overflow-x-auto custom-scrollbar pb-2">
                        <div className="min-w-max p-4 flex flex-col gap-2 bg-slate-50 rounded-xl border border-slate-200">
                          {/* Hàng 1 (Dãy trên - ngoài cùng) */}
                          <div className="flex gap-2">
                            {seatRows.map((row, rIdx) => {
                              const seat = row[0];
                              if (!seat) return <div key={`empty-0-${rIdx}`} className="w-10 shrink-0" />;
                              return (
                                <div key={seat.seat_id} className="w-10 shrink-0">
                                  <SeatButton seat={seat} selected={pickedSeatIds.has(seat.seat_id)} onClick={toggleSeat} />
                                </div>
                              );
                            })}
                          </div>

                          {/* Hàng 2 (Dãy trên - phía trong) */}
                          <div className="flex gap-2">
                            {seatRows.map((row, rIdx) => {
                              const seat = row[1];
                              if (!seat) return <div key={`empty-1-${rIdx}`} className="w-10 shrink-0" />;
                              return (
                                <div key={seat.seat_id} className="w-10 shrink-0">
                                  <SeatButton seat={seat} selected={pickedSeatIds.has(seat.seat_id)} onClick={toggleSeat} />
                                </div>
                              );
                            })}
                          </div>

                          {/* Lối đi ở giữa */}
                          <div className="h-6 flex items-center relative my-1 bg-slate-200/50 rounded border-y border-slate-200/80 w-full">
                            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                              <span className="text-[9px] font-black uppercase tracking-[0.25em] text-slate-400">Lối đi</span>
                            </div>
                          </div>

                          {/* Hàng 3 (Dãy dưới - phía trong) */}
                          <div className="flex gap-2">
                            {seatRows.map((row, rIdx) => {
                              const seat = row[2];
                              if (!seat) return <div key={`empty-2-${rIdx}`} className="w-10 shrink-0" />;
                              return (
                                <div key={seat.seat_id} className="w-10 shrink-0">
                                  <SeatButton seat={seat} selected={pickedSeatIds.has(seat.seat_id)} onClick={toggleSeat} />
                                </div>
                              );
                            })}
                          </div>

                          {/* Hàng 4 (Dãy dưới - ngoài cùng) */}
                          <div className="flex gap-2">
                            {seatRows.map((row, rIdx) => {
                              const seat = row[3];
                              if (!seat) return <div key={`empty-3-${rIdx}`} className="w-10 shrink-0" />;
                              return (
                                <div key={seat.seat_id} className="w-10 shrink-0">
                                  <SeatButton seat={seat} selected={pickedSeatIds.has(seat.seat_id)} onClick={toggleSeat} />
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                    );
                  })()
                )}
              </div>
            ) : (
              <div className="h-36 rounded-xl border border-dashed border-outline-variant flex items-center justify-center text-xs font-semibold text-on-surface-variant">
                Chọn toa để xem ghế từ database.
              </div>
            )}
          </div>

          <RouteMap
            title={`Bản đồ tải chặng ${selectedPlan ? `· ${selectedPlan.origin_code} - ${selectedPlan.destination_code}` : ""}`}
            segments={routeSegments}
            loading={loadingPlans}
            selectedOrigin={origin}
            selectedDestination={destination}
          />
        </section>

        <aside className="col-span-12 lg:col-span-4 space-y-6">
          <div className="bg-white border border-outline-variant rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="font-bold text-sm text-on-surface flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-sm">search</span>
              Tìm kiếm hành trình
            </h3>
            <div className="grid grid-cols-2 gap-2">
              <SearchableStationSelect label="Ga đi" options={allStations} value={origin} onChange={(value) => { setOrigin(value); setSelectedTripId(null); setPickedSeats([]); setIsCombinedMode(false); setCombinedLegs([]); }} />
              <SearchableStationSelect label="Ga đến" align="right" options={destinationStations} value={destination} onChange={(value) => { setDestination(value); setSelectedTripId(null); setPickedSeats([]); setIsCombinedMode(false); setCombinedLegs([]); }} />
            </div>
            <div className="space-y-1">
              <DateField label="Ngày đi" value={departureDate} onChange={setDepartureDate} dates={bookingOptions?.departure_dates ?? []} loading={loadingOptions} />
            </div>
            <div className="pt-2">
              {isCombinedMode ? (
                <button
                  type="button"
                  onClick={() => {
                    setIsCombinedMode(false);
                    setPickedSeats([]);
                    setCombinedLegs([]);
                  }}
                  className="w-full py-1.5 bg-slate-100 hover:bg-slate-200/80 text-slate-700 font-extrabold text-[10.5px] rounded-lg transition-all cursor-pointer border border-outline-variant/35"
                >
                  ✕ Hủy chế độ vé ghép AI
                </button>
              ) : (
                <button
                  type="button"
                  onClick={triggerCombinedMode}
                  className="w-full py-1.5 bg-primary hover:bg-primary/95 text-white font-extrabold text-[10.5px] rounded-lg transition-all shadow-sm cursor-pointer"
                >
                  💡 Đề xuất vé ghép chặng AI
                </button>
              )}
            </div>
          </div>

          <div className="bg-white border border-outline-variant rounded-xl p-6 shadow-sm">
            <h3 className="font-bold text-sm text-on-surface mb-3 flex items-center gap-2 border-b border-outline-variant/30 pb-2">
              <span className="material-symbols-outlined text-primary text-sm">shopping_bag</span>
              Chi tiết vé đặt
            </h3>
            <div className="space-y-3 text-xs font-semibold">
              <SummaryRow label="Hành trình" value={`${origin} - ${destination}`} />
              <SummaryRow label="Chuyến tàu" value={selectedPlan?.train_code ?? "Chưa chọn"} />
              {isCombinedMode ? (
                <>
                  <div className="p-3 bg-purple-50/70 border border-purple-200 rounded-xl space-y-2.5 text-[11px] font-semibold text-slate-700">
                    <span className="text-[10px] text-purple-700 font-black uppercase block tracking-wider">Hành trình chặng ghép AI</span>
                    {combinedLegs.map((legItem, idx) => (
                      <div key={idx} className="border-b border-purple-100/50 pb-1.5 last:border-0 last:pb-0 space-y-0.5">
                        <p className="font-black text-xs text-on-surface">{legItem.leg} ({legItem.time})</p>
                        <p className="text-on-surface-variant font-semibold">Toa: Toa 02 • Vị trí: <span className="text-purple-700 font-extrabold">{legItem.seatNo}</span></p>
                        {legItem.note && <p className="text-[9.5px] text-amber-700 font-bold italic mt-0.5">{legItem.note}</p>}
                      </div>
                    ))}
                  </div>
                  <div className="flex justify-between items-end pt-2">
                    <span className="text-on-surface-variant font-bold">Giá vé ghép</span>
                    <span className="text-xs font-black text-amber-700">Chờ backend báo giá</span>
                  </div>
                  <Button className="w-full py-2.5" disabled>
                    Đặt vé ghép chưa được backend hỗ trợ
                  </Button>
                </>
              ) : (
                <>
                  <SummaryRow label="Toa" value={selectedCoachNo || "Chưa chọn"} />
                  <SummaryRow label="Loại chỗ" value={selectedProduct?.seat_type_name ?? "Chưa chọn"} />
                  <SummaryRow label="Số ghế" value={pickedSeats.length ? pickedSeats.map((item) => `Toa ${item.coachNo}-${item.seatNo}`).join(", ") : "Chưa chọn"} />
                  <div className="flex justify-between items-end pt-2">
                    <span className="text-on-surface-variant font-bold">Tạm tính</span>
                    <span className="text-lg font-black text-primary font-mono">{moneyFormatter.format(estimatedTotal)}</span>
                  </div>
                  <Button className="w-full py-2.5" disabled={pickedSeats.length === 0 || booking} onClick={handleConfirm}>
                    {booking ? "Đang giữ chỗ..." : "Xác nhận và đặt vé"}
                  </Button>
                </>
              )}
              {confirmed.length > 0 ? (
                <div className="rounded-lg bg-green-50 border border-green-200 p-3 text-green-800 space-y-1">
                  <p className="font-black">Đã đặt {confirmed.length} vé trong phiên này</p>
                  {confirmed.map((item) => (
                    <div key={item.booking_id} className="flex items-center justify-between gap-2">
                      <p className="font-mono">{item.booking_code} · Toa {item.coach_no} · Ghế {item.seat_no}</p>
                      <Link href={`/ticket-details?code=${encodeURIComponent(item.booking_code)}`} className="shrink-0 font-bold text-primary hover:underline">
                        Xem vé
                      </Link>
                    </div>
                  ))}
                  <p className="border-t border-green-200 pt-1 font-bold">Tổng đã thanh toán: {moneyFormatter.format(paidPrice)}</p>
                </div>
              ) : null}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}

function SeatButton({ seat, selected, onClick, suffix }: { seat: BookingSeat; selected: boolean; onClick: (seat: BookingSeat) => void; suffix?: string }) {
  const unavailable = seat.status !== "available";
  return (
    <button type="button" disabled={unavailable} onClick={() => onClick(seat)} title={`Ghế ${seat.seat_no} · ${seat.status}`} className={`h-10 w-full rounded-md text-[9px] font-black transition-all relative ${selected ? "bg-primary text-white shadow-md scale-105" : unavailable ? "bg-slate-300 text-slate-500 cursor-not-allowed" : "bg-white border border-outline-variant hover:border-primary text-on-surface"}`}>
      {seat.seat_no}
      {suffix ? <span className="block text-[7px] opacity-70">{suffix}</span> : null}
    </button>
  );
}

const BOOKING_DATE_MIN = "2024-01-01";
const BOOKING_DATE_MAX = "2025-12-30";

function toDD(iso: string) {
  if (!iso) return "";
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}

function fromDD(display: string, allowedDates: string[]): string | null {
  const match = display.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (!match) return null;
  const [, d, m, y] = match;
  const iso = `${y}-${m}-${d}`;
  if (iso < BOOKING_DATE_MIN || iso > BOOKING_DATE_MAX) return null;
  // Nếu có danh sách ngày hợp lệ thì phải nằm trong đó
  if (allowedDates.length > 0 && !allowedDates.includes(iso)) return null;
  return iso;
}

function DateField({ label, value, onChange, dates, loading, optional }: { label: string; value: string; onChange: (value: string) => void; dates: string[]; loading?: boolean; optional?: boolean }) {
  const [display, setDisplay] = useState(toDD(value));
  const hiddenDateInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setDisplay(toDD(value));
  }, [value]);

  return (
    <div className="space-y-1">
      <label className="text-[9px] uppercase font-bold text-on-surface-variant">{label} <span className="normal-case font-normal opacity-60">(dd/mm/yyyy)</span></label>
      <div className="relative flex items-center">
        <input
          type="text"
          placeholder="dd/mm/yyyy"
          maxLength={10}
          value={display}
          disabled={loading}
          onChange={(e) => {
            setDisplay(e.target.value);
            const iso = fromDD(e.target.value, dates);
            if (iso) onChange(iso);
          }}
          onBlur={() => {
            const iso = fromDD(display, dates);
            if (!iso) setDisplay(toDD(value));
          }}
          className="w-full rounded-lg border border-outline-variant bg-surface-container-low pl-2 pr-8 py-2 text-xs font-semibold disabled:opacity-50 outline-none focus:ring-1 focus:ring-primary text-on-surface"
        />
        <span
          onClick={() => {
            if (hiddenDateInputRef.current && typeof hiddenDateInputRef.current.showPicker === "function") {
              hiddenDateInputRef.current.showPicker();
            }
          }}
          className="absolute right-2 material-symbols-outlined text-outline text-sm cursor-pointer hover:text-primary transition-colors select-none"
        >
          calendar_today
        </span>
        <input
          ref={hiddenDateInputRef}
          type="date"
          tabIndex={-1}
          min={dates.length > 0 ? dates[0] : BOOKING_DATE_MIN}
          max={dates.length > 0 ? dates.at(-1) : BOOKING_DATE_MAX}
          value={value}
          disabled={loading}
          onChange={(e) => { if (e.target.value) onChange(e.target.value); }}
          className="absolute pointer-events-none opacity-0"
          style={{ width: 0, height: 0 }}
        />
      </div>
      {optional && dates.length === 0 ? <span className="text-[8px] text-amber-700">Chưa có dữ liệu</span> : null}
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return <div className="flex justify-between gap-3 py-1 border-b border-outline-variant/20"><span className="text-on-surface-variant font-medium">{label}</span><span className="text-right text-on-surface">{value}</span></div>;
}
