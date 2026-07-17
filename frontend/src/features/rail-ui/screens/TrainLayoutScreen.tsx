"use client";

import React from "react";

export function TrainLayoutScreen() {
  return (
    <div className="space-y-6">
      {/* Header Section with Quick Stats */}
      <section className="flex justify-end items-end mb-6">
        <div className="flex gap-2">
          <button className="px-6 py-2 border border-primary text-primary font-bold rounded-lg hover:bg-primary/5 transition-all text-xs">
            Segmenting
          </button>
          <button className="px-6 py-2 bg-primary text-on-primary font-bold rounded-lg hover:brightness-110 transition-all text-xs shadow-md">
            Reallocating Quotas
          </button>
        </div>
      </section>

      {/* Bento Grid Layout */}
      <div className="grid grid-cols-12 gap-6">
        {/* Train Capacity Map (Full Width Visual) */}
        <div className="col-span-12 bg-white border border-outline-variant rounded-xl p-6 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-bold text-on-surface flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">train</span>
              Train Capacity Map: High-Speed Unit #8421
            </h3>
            <div className="flex gap-4 text-xs font-semibold">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-primary rounded-sm" />
                Reserved
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-secondary-container rounded-sm" />
                Available
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-error-container rounded-sm" />
                High Bid Lock
              </div>
            </div>
          </div>

          <div className="flex gap-2 overflow-x-auto pb-4 custom-scrollbar">
            {/* Engine */}
            <div className="min-w-[80px] h-20 bg-slate-100 rounded-l-full flex items-center justify-center border-2 border-slate-200">
              <span className="material-symbols-outlined text-slate-400 text-2xl">speed</span>
            </div>

            {/* Car 1 (First Class) */}
            <div className="min-w-[140px] h-20 bg-surface-container-low border border-primary/20 rounded-lg p-2 train-car flex flex-col justify-between cursor-pointer">
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-bold text-primary">CAR 01 (F)</span>
                <span className="text-[10px] px-1 bg-primary-container text-white rounded font-bold">92%</span>
              </div>
              <div className="grid grid-cols-4 gap-1">
                <div className="h-2 bg-primary rounded-full" />
                <div className="h-2 bg-primary rounded-full" />
                <div className="h-2 bg-primary rounded-full" />
                <div className="h-2 bg-secondary-container rounded-full" />
                <div className="h-2 bg-primary rounded-full" />
                <div className="h-2 bg-primary rounded-full" />
                <div className="h-2 bg-primary rounded-full" />
                <div className="h-2 bg-primary rounded-full" />
              </div>
            </div>

            {/* Car 2 (First Class) */}
            <div className="min-w-[140px] h-20 bg-surface-container-low border border-primary/20 rounded-lg p-2 train-car flex flex-col justify-between cursor-pointer">
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-bold text-primary">CAR 02 (F)</span>
                <span className="text-[10px] px-1 bg-primary-container text-white rounded font-bold">78%</span>
              </div>
              <div className="grid grid-cols-4 gap-1">
                <div className="h-2 bg-primary rounded-full" />
                <div className="h-2 bg-secondary-container rounded-full" />
                <div className="h-2 bg-primary rounded-full" />
                <div className="h-2 bg-primary rounded-full" />
                <div className="h-2 bg-primary rounded-full" />
                <div className="h-2 bg-primary rounded-full" />
                <div className="h-2 bg-secondary-container rounded-full" />
                <div className="h-2 bg-secondary-container rounded-full" />
              </div>
            </div>

            {/* Car 3 (Bar) */}
            <div className="min-w-[100px] h-20 bg-tertiary-fixed rounded-lg p-2 flex flex-col items-center justify-center border border-outline-variant">
              <span className="material-symbols-outlined text-on-tertiary-fixed-variant text-xl">local_cafe</span>
              <span className="text-[8px] font-bold uppercase mt-1">Bistro</span>
            </div>

            {/* Cars 4-6 (Standard) */}
            <div className="flex gap-2">
              <div className="min-w-[140px] h-20 bg-white border border-outline-variant rounded-lg p-2 train-car flex flex-col justify-between cursor-pointer">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-bold text-on-surface-variant">CAR 04</span>
                  <span className="text-[10px] px-1 bg-error-container text-error rounded font-bold">98%</span>
                </div>
                <div className="grid grid-cols-4 gap-1">
                  <div className="h-2 bg-primary rounded-full" />
                  <div className="h-2 bg-primary rounded-full" />
                  <div className="h-2 bg-error-container rounded-full" />
                  <div className="h-2 bg-primary rounded-full" />
                  <div className="h-2 bg-primary rounded-full" />
                  <div className="h-2 bg-primary rounded-full" />
                  <div className="h-2 bg-primary rounded-full" />
                  <div className="h-2 bg-primary rounded-full" />
                </div>
              </div>

              <div className="min-w-[140px] h-20 bg-white border border-outline-variant rounded-lg p-2 train-car flex flex-col justify-between cursor-pointer">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-bold text-on-surface-variant">CAR 05</span>
                  <span className="text-[10px] px-1 bg-secondary-container text-on-secondary-container rounded font-bold">45%</span>
                </div>
                <div className="grid grid-cols-4 gap-1">
                  <div className="h-2 bg-primary rounded-full" />
                  <div className="h-2 bg-secondary-container rounded-full" />
                  <div className="h-2 bg-secondary-container rounded-full" />
                  <div className="h-2 bg-secondary-container rounded-full" />
                  <div className="h-2 bg-primary rounded-full" />
                  <div className="h-2 bg-primary rounded-full" />
                  <div className="h-2 bg-secondary-container rounded-full" />
                  <div className="h-2 bg-secondary-container rounded-full" />
                </div>
              </div>

              <div className="min-w-[140px] h-20 bg-white border border-outline-variant rounded-lg p-2 train-car flex flex-col justify-between cursor-pointer">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-bold text-on-surface-variant">CAR 06</span>
                  <span className="text-[10px] px-1 bg-secondary-container text-on-secondary-container rounded font-bold">62%</span>
                </div>
                <div className="grid grid-cols-4 gap-1">
                  <div className="h-2 bg-primary rounded-full" />
                  <div className="h-2 bg-primary rounded-full" />
                  <div className="h-2 bg-secondary-container rounded-full" />
                  <div className="h-2 bg-secondary-container rounded-full" />
                  <div className="h-2 bg-primary rounded-full" />
                  <div className="h-2 bg-primary rounded-full" />
                  <div className="h-2 bg-primary rounded-full" />
                  <div className="h-2 bg-secondary-container rounded-full" />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Seat Inventory Table (Left Side) */}
        <div className="col-span-12 lg:col-span-8 bg-white border border-outline-variant rounded-xl overflow-hidden shadow-sm">
          <div className="p-6 border-b border-outline-variant flex justify-between items-center">
            <h3 className="font-bold text-on-surface">Seat Inventory Allocation</h3>
            <div className="flex gap-2">
              <span className="px-2 py-1 bg-surface-container-low text-primary rounded text-[10px] font-bold">
                LONG LEG (80%)
              </span>
              <span className="px-2 py-1 bg-secondary-container text-on-secondary-container rounded text-[10px] font-bold">
                SHORT LEG (20%)
              </span>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-surface-container-low text-on-surface-variant font-bold text-xs">
                <tr>
                  <th className="px-6 py-4">SEGMENT</th>
                  <th class="px-6 py-4">CLASS</th>
                  <th class="px-6 py-4">ALLOCATED</th>
                  <th class="px-6 py-4">BOOKED</th>
                  <th class="px-6 py-4">BID PRICE</th>
                  <th class="px-6 py-4 text-right">OPTIMIZATION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant text-sm">
                <tr className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 font-semibold text-on-surface">Paris → Marseille (Long)</td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-0.5 border border-primary/30 text-primary text-[10px] rounded font-bold uppercase">
                      Business
                    </span>
                  </td>
                  <td className="px-6 py-4 text-on-surface-variant font-medium">120 Seats</td>
                  <td className="px-6 py-4">
                    <div className="w-full bg-slate-100 h-1.5 rounded-full mt-1">
                      <div className="bg-primary h-1.5 rounded-full" style={{ width: "85%" }} />
                    </div>
                    <span className="text-[10px] text-on-surface-variant font-semibold">102 / 120 (85%)</span>
                  </td>
                  <td className="px-6 py-4 font-mono font-bold">€245.00</td>
                  <td className="px-6 py-4 text-right">
                    <span className="text-error font-bold text-[11px]">+12.4% Recommended</span>
                  </td>
                </tr>
                <tr className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 font-semibold text-on-surface">Paris → Lyon (Short)</td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-0.5 border border-primary/30 text-primary text-[10px] rounded font-bold uppercase">
                      Standard
                    </span>
                  </td>
                  <td className="px-6 py-4 text-on-surface-variant font-medium">400 Seats</td>
                  <td className="px-6 py-4">
                    <div className="w-full bg-slate-100 h-1.5 rounded-full mt-1">
                      <div className="bg-primary h-1.5 rounded-full" style={{ width: "42%" }} />
                    </div>
                    <span className="text-[10px] text-on-surface-variant font-semibold">168 / 400 (42%)</span>
                  </td>
                  <td className="px-6 py-4 font-mono font-bold">€89.00</td>
                  <td className="px-6 py-4 text-right">
                    <span className="text-primary font-bold text-[11px]">-5.0% Flash Sale</span>
                  </td>
                </tr>
                <tr className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 font-semibold text-on-surface">Lyon → Marseille (Short)</td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-0.5 border border-primary/30 text-primary text-[10px] rounded font-bold uppercase">
                      Standard
                    </span>
                  </td>
                  <td className="px-6 py-4 text-on-surface-variant font-medium">400 Seats</td>
                  <td className="px-6 py-4">
                    <div className="w-full bg-slate-100 h-1.5 rounded-full mt-1">
                      <div className="bg-primary h-1.5 rounded-full" style={{ width: "95%" }} />
                    </div>
                    <span className="text-[10px] text-on-surface-variant font-semibold">380 / 400 (95%)</span>
                  </td>
                  <td className="px-6 py-4 font-mono font-bold">€115.00</td>
                  <td className="px-6 py-4 text-right">
                    <span className="text-error font-bold text-[11px]">Cap Reached</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Gap Combining & Recommendations (Right Side) */}
        <div className="col-span-12 lg:col-span-4 space-y-6">
          {/* AI Recommendation Card */}
          <div className="bg-white border-l-4 border-primary border-y border-r border-outline-variant rounded-xl p-6 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 right-0 p-2 opacity-5">
              <span className="material-symbols-outlined text-6xl">auto_awesome</span>
            </div>
            <div className="flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-primary text-sm">auto_awesome</span>
              <h3 className="font-bold text-on-surface">Gap Combining Opportunities</h3>
            </div>
            <p className="text-xs text-on-surface-variant mb-4 leading-relaxed font-semibold">
              AI found 12 available "gaps" that can be merged into new end-to-end tickets.
            </p>
            <div className="space-y-3">
              <div className="p-3 bg-surface-container-low rounded-lg border border-primary/10">
                <div className="flex justify-between items-start mb-2">
                  <span className="font-bold text-xs text-on-surface">Paris-Lyon + Lyon-Marseille</span>
                  <span className="text-primary font-bold text-xs">€1,240 Est. Gain</span>
                </div>
                <p className="text-[11px] text-on-surface-variant leading-relaxed font-medium">
                  4 Seats free in Car 5 across both segments. Auto-merge recommended.
                </p>
                <button className="mt-2 w-full py-1.5 bg-primary/10 text-primary font-bold text-[10px] rounded hover:bg-primary/20 transition-all">
                  Execute Merge
                </button>
              </div>

              <div className="p-3 bg-surface-container-low rounded-lg border border-primary/10">
                <div className="flex justify-between items-start mb-2">
                  <span className="font-bold text-xs text-on-surface">Lille-Paris + Paris-Nice</span>
                  <span className="text-primary font-bold text-xs">€890 Est. Gain</span>
                </div>
                <p className="text-[11px] text-on-surface-variant leading-relaxed font-medium">
                  2 Business class seats align perfectly at Gare de Lyon node.
                </p>
                <button className="mt-2 w-full py-1.5 bg-primary/10 text-primary font-bold text-[10px] rounded hover:bg-primary/20 transition-all">
                  Execute Merge
                </button>
              </div>
            </div>
          </div>

          {/* Bid Price Trend Chart */}
          <div className="bg-white border border-outline-variant rounded-xl p-6 shadow-sm">
            <div className="flex justify-between items-center mb-6">
              <h3 className="font-bold text-on-surface">Bid Price Trend</h3>
              <span className="material-symbols-outlined text-on-surface-variant">show_chart</span>
            </div>
            <div className="h-40 w-full relative flex items-end gap-2 px-2">
              <div className="flex-1 bg-primary/20 h-[40%] rounded-t-sm relative group cursor-pointer hover:bg-primary transition-all">
                <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px] font-bold hidden group-hover:block whitespace-nowrap">
                  €180
                </div>
              </div>
              <div className="flex-1 bg-primary/20 h-[55%] rounded-t-sm relative group cursor-pointer hover:bg-primary transition-all">
                <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px] font-bold hidden group-hover:block whitespace-nowrap">
                  €195
                </div>
              </div>
              <div className="flex-1 bg-primary/20 h-[75%] rounded-t-sm relative group cursor-pointer hover:bg-primary transition-all">
                <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px] font-bold hidden group-hover:block whitespace-nowrap">
                  €210
                </div>
              </div>
              <div className="flex-1 bg-primary/20 h-[60%] rounded-t-sm relative group cursor-pointer hover:bg-primary transition-all">
                <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px] font-bold hidden group-hover:block whitespace-nowrap">
                  €200
                </div>
              </div>
              <div className="flex-1 bg-primary h-[90%] rounded-t-sm relative group cursor-pointer bid-price-indicator">
                <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px] font-bold">
                  €245
                </div>
              </div>
              <div className="flex-1 bg-primary/20 h-[85%] rounded-t-sm relative group cursor-pointer hover:bg-primary transition-all" />
              <div className="flex-1 bg-primary/20 h-[95%] rounded-t-sm relative group cursor-pointer hover:bg-primary transition-all" />
            </div>
            <div className="flex justify-between mt-2 text-[10px] text-on-surface-variant font-bold">
              <span>T-30 Days</span>
              <span>Today</span>
              <span>Departure</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
