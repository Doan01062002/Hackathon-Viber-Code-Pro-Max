"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { SearchableStationSelect } from "@/components/ui/SearchableStationSelect";
import {
  confirmBooking,
  createBookingHold,
  getBookingOptions,
  getBookingSeatPlan,
  searchBookingProducts,
} from "@/features/booking/api/bookingApi";
import { CombinedBookingPanel } from "@/features/booking/components/CombinedBookingPanel";
import { CombinedJourneyMap } from "@/features/booking/components/CombinedJourneyMap";
import { useCombinedBooking } from "@/features/booking/hooks/useCombinedBooking";
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
  // Luồng vé ghép sống ở hook riêng; sơ đồ hành trình và cột phải cùng đọc state này.
  const combined = useCombinedBooking();

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
  };

  const exitCombinedMode = () => {
    setIsCombinedMode(false);
    setPickedSeats([]);
  };

  /** Chặng của phương án đang xem: ưu tiên nhóm vé đã giữ, nếu chưa thì phương án đang chọn. */
  const combinedLegs = combined.state.booking?.legs ?? combined.selectedOption?.legs ?? [];
  const combinedTotal =
    combined.state.booking?.total_price ?? combined.selectedOption?.estimated_total_price ?? null;

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
              <CombinedJourneyMap
                legs={combinedLegs}
                totalPrice={combinedTotal}
                emptyHint="Chọn một phương án ghép chặng ở cột bên phải để xem sơ đồ hành trình."
              />
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
              <SearchableStationSelect label="Ga đi" options={allStations} value={origin} onChange={(value) => { setOrigin(value); setSelectedTripId(null); setPickedSeats([]); setIsCombinedMode(false); }} />
              <SearchableStationSelect label="Ga đến" align="right" options={destinationStations} value={destination} onChange={(value) => { setDestination(value); setSelectedTripId(null); setPickedSeats([]); setIsCombinedMode(false); }} />
            </div>
            <div className="space-y-1">
              <DateField label="Ngày đi" value={departureDate} onChange={setDepartureDate} dates={bookingOptions?.departure_dates ?? []} loading={loadingOptions} />
            </div>
            <div className="pt-2">
              {isCombinedMode ? null : (
                <button
                  type="button"
                  onClick={triggerCombinedMode}
                  className="w-full py-1.5 bg-primary hover:bg-primary/95 text-white font-extrabold text-[10.5px] rounded-lg transition-all shadow-sm cursor-pointer"
                >
                  💡 Tìm vé ghép chặng
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
                <CombinedBookingPanel
                  combined={combined}
                  origin={origin}
                  destination={destination}
                  serviceDate={departureDate}
                  onExit={exitCombinedMode}
                />
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

function DateField({ label, value, onChange, dates, loading, optional }: { label: string; value: string; onChange: (value: string) => void; dates: string[]; loading?: boolean; optional?: boolean }) {
  return (
    <div className="space-y-1">
      <label className="text-[9px] uppercase font-bold text-on-surface-variant">{label}</label>
      <input type="date" value={value} disabled={loading || dates.length === 0} min={dates[0]} max={dates.at(-1)} onChange={(event) => onChange(event.target.value)} className="w-full rounded-lg border border-outline-variant bg-surface-container-low px-2 py-2 text-xs font-semibold disabled:opacity-50" />
      {optional && dates.length === 0 ? <span className="text-[8px] text-amber-700">Chưa có dữ liệu</span> : null}
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return <div className="flex justify-between gap-3 py-1 border-b border-outline-variant/20"><span className="text-on-surface-variant font-medium">{label}</span><span className="text-right text-on-surface">{value}</span></div>;
}
