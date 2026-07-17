"use client";

import React from "react";

export function DashboardScreen() {
  return (
    <div className="space-y-6">
      {/* Dashboard Header / Controls */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-3xl font-black text-on-surface">
            Overview Dashboard
          </h2>
          <p className="text-sm text-on-surface-variant">
            Capacity & Yield management console for network operations
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="bg-surface border border-outline-variant rounded-lg px-3 py-1.5 flex items-center space-x-2">
            <span className="material-symbols-outlined text-outline text-sm">calendar_today</span>
            <span className="text-xs font-semibold">Today, 17 July 2026</span>
          </div>
          <select
            className="bg-surface border border-outline-variant rounded-lg px-3 py-1.5 text-xs font-semibold focus:ring-primary focus:border-primary outline-none"
            defaultValue="Train ID: SE1, SE2, SE3"
          >
            <option>Train ID: SE1, SE2, SE3</option>
            <option>Train ID: SE4, SE5, SE6</option>
          </select>
        </div>
      </div>

      {/* 4 Key Metric Cards (Bento Style) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        {/* Metric Card 1 */}
        <div className="bg-surface border border-outline-variant p-5 rounded-xl hover:bg-surface-container-low transition-colors duration-200">
          <div className="flex justify-between items-start mb-4">
            <span className="text-[10px] tracking-wider uppercase font-bold text-on-surface-variant">
              Total Revenue
            </span>
            <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-[10px] font-bold">
              +12.4%
            </span>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-black text-on-surface">$1.24M</span>
            <span className="text-on-surface-variant text-xs">USD</span>
          </div>
          <div className="mt-4 h-12 w-full">
            {/* Sparkline Mockup */}
            <svg className="w-full h-full overflow-visible" viewBox="0 0 100 20">
              <path
                d="M0 15 L10 12 L20 16 L30 10 L40 14 L50 8 L60 12 L70 5 L80 10 L90 2 L100 5"
                fill="none"
                stroke="#3525cd"
                strokeLinecap="round"
                strokeWidth="2"
              />
            </svg>
          </div>
        </div>

        {/* Metric Card 2 */}
        <div className="bg-surface border border-outline-variant p-5 rounded-xl hover:bg-surface-container-low transition-colors duration-200">
          <div className="flex justify-between items-start mb-4">
            <span className="text-[10px] tracking-wider uppercase font-bold text-on-surface-variant">
              Avg Load Factor
            </span>
            <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded text-[10px] font-bold">
              -2.1%
            </span>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-black text-on-surface">84.2%</span>
          </div>
          <div className="mt-4 h-12 w-full">
            <svg className="w-full h-full overflow-visible" viewBox="0 0 100 20">
              <path
                d="M0 5 L10 8 L20 4 L30 12 L40 10 L50 15 L60 13 L70 18 L80 15 L90 19 L100 16"
                fill="none"
                stroke="#ba1a1a"
                strokeLinecap="round"
                strokeWidth="2"
              />
            </svg>
          </div>
        </div>

        {/* Metric Card 3 */}
        <div className="bg-surface border border-outline-variant p-5 rounded-xl hover:bg-surface-container-low transition-colors duration-200">
          <div className="flex justify-between items-start mb-4">
            <span className="text-[10px] tracking-wider uppercase font-bold text-on-surface-variant">
              Seat-km Utilization
            </span>
            <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-[10px] font-bold">
              +5.8%
            </span>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-black text-on-surface">0.92</span>
            <span className="text-on-surface-variant text-xs">ASK</span>
          </div>
          <div className="mt-4 h-12 w-full">
            <svg className="w-full h-full overflow-visible" viewBox="0 0 100 20">
              <path
                d="M0 18 L20 12 L40 15 L60 8 L80 10 L100 2"
                fill="none"
                stroke="#3525cd"
                strokeLinecap="round"
                strokeWidth="2"
              />
            </svg>
          </div>
        </div>

        {/* Metric Card 4: AI Insight Style */}
        <div className="bg-surface-container border border-primary/20 p-5 rounded-xl ai-accent-border hover:bg-surface-container-high transition-colors duration-200">
          <div className="flex justify-between items-start mb-4">
            <span className="text-[10px] tracking-wider uppercase text-primary font-bold">
              Unfulfilled Demand
            </span>
            <span className="material-symbols-outlined text-primary scale-75">
              auto_awesome
            </span>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-black text-primary">4,122</span>
            <span className="text-primary/70 text-xs">Seats</span>
          </div>
          <p className="mt-2 text-[11px] text-on-surface-variant leading-tight font-medium">
            AI recommends adding capacity to SE3 for HN-Vinh segment on weekend.
          </p>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Revenue & Load Factor Dual Axis */}
        <div className="lg:col-span-2 bg-white border border-outline-variant rounded-xl p-6">
          <div className="flex justify-between items-center mb-8">
            <h3 className="text-base font-bold text-on-surface">
              Revenue & Load Factor Trends
            </h3>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-primary" />
                <span className="text-xs text-on-surface-variant">Revenue</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-secondary" />
                <span className="text-xs text-on-surface-variant">Load Factor</span>
              </div>
            </div>
          </div>
          <div className="h-64 relative w-full flex items-end justify-between px-2">
            {/* Fake Chart Grid Lines */}
            <div className="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-10">
              <div className="border-t border-black w-full" />
              <div className="border-t border-black w-full" />
              <div className="border-t border-black w-full" />
              <div className="border-t border-black w-full" />
            </div>
            {/* Bars & Line Overlay Mockup */}
            <div className="relative w-full h-full flex items-end justify-around">
              <div className="w-8 bg-primary/20 rounded-t h-[40%] relative">
                <div className="absolute -top-1 left-0 w-full h-1 bg-secondary rounded-full" />
              </div>
              <div className="w-8 bg-primary/20 rounded-t h-[55%] relative">
                <div className="absolute -top-4 left-0 w-full h-1 bg-secondary rounded-full" />
              </div>
              <div className="w-8 bg-primary/20 rounded-t h-[45%] relative">
                <div className="absolute -top-2 left-0 w-full h-1 bg-secondary rounded-full" />
              </div>
              <div className="w-8 bg-primary/30 rounded-t h-[70%] relative">
                <div className="absolute -top-8 left-0 w-full h-1 bg-secondary rounded-full" />
              </div>
              <div className="w-8 bg-primary/40 rounded-t h-[85%] relative">
                <div className="absolute -top-2 left-0 w-full h-1 bg-secondary rounded-full" />
              </div>
              <div className="w-8 bg-primary/30 rounded-t h-[60%] relative">
                <div className="absolute -top-6 left-0 w-full h-1 bg-secondary rounded-full" />
              </div>
              <div className="w-8 bg-primary/20 rounded-t h-[50%] relative">
                <div className="absolute -top-1 left-0 w-full h-1 bg-secondary rounded-full" />
              </div>
              <div className="w-8 bg-primary/30 rounded-t h-[65%] relative">
                <div className="absolute -top-5 left-0 w-full h-1 bg-secondary rounded-full" />
              </div>
            </div>
          </div>
          <div className="flex justify-between mt-4 px-2 text-[10px] text-on-surface-variant uppercase font-bold">
            <span>Mon</span>
            <span>Tue</span>
            <span>Wed</span>
            <span>Thu</span>
            <span>Fri</span>
            <span>Sat</span>
            <span>Sun</span>
            <span>Mon</span>
          </div>
        </div>

        {/* Route Heatmap */}
        <div className="bg-white border border-outline-variant rounded-xl p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-on-surface mb-6">
              Route Heatmap
            </h3>
            <div className="space-y-6">
              {/* Segment */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-on-surface-variant font-medium">HN → Vinh</span>
                  <span className="font-bold text-primary">92% LF</span>
                </div>
                <div className="h-3 w-full bg-surface-container rounded-full overflow-hidden">
                  <div className="h-full bg-primary" style={{ width: "92%" }} />
                </div>
              </div>
              {/* Segment */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-on-surface-variant font-medium">Vinh → Hue</span>
                  <span className="font-bold text-primary">78% LF</span>
                </div>
                <div className="h-3 w-full bg-surface-container rounded-full overflow-hidden">
                  <div className="h-full bg-primary" style={{ width: "78%" }} />
                </div>
              </div>
              {/* Segment */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-on-surface-variant font-medium">Hue → DN</span>
                  <span className="font-bold text-red-600">98% LF</span>
                </div>
                <div className="h-3 w-full bg-surface-container rounded-full overflow-hidden">
                  <div className="h-full bg-red-500" style={{ width: "98%" }} />
                </div>
              </div>
              {/* Segment */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-on-surface-variant font-medium">DN → SG</span>
                  <span className="font-bold text-primary">64% LF</span>
                </div>
                <div className="h-3 w-full bg-surface-container rounded-full overflow-hidden">
                  <div className="h-full bg-primary" style={{ width: "64%" }} />
                </div>
              </div>
            </div>
          </div>

          <div className="mt-8 p-4 bg-surface-container-low rounded-lg border border-dashed border-outline-variant">
            <p className="text-[11px] text-on-surface-variant italic leading-relaxed">
              Critical bottleneck detected at <span className="font-bold">Hue-DN</span>. Higher yield available through segment re-allocation.
            </p>
          </div>
        </div>
      </div>

      {/* Table Row: Trains at Risk */}
      <div className="bg-white border border-outline-variant rounded-xl overflow-hidden shadow-sm">
        <div className="p-6 border-b border-outline-variant flex justify-between items-center">
          <h3 className="text-base font-bold text-on-surface">
            Trains at Risk
          </h3>
          <button className="text-xs font-bold text-primary flex items-center space-x-1 hover:underline">
            <span>View all warnings</span>
            <span className="material-symbols-outlined text-sm">chevron_right</span>
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-surface-container-low border-b border-outline-variant text-[11px] text-on-surface-variant uppercase font-bold">
                <th className="px-6 py-4">Train ID</th>
                <th className="px-6 py-4">Departure</th>
                <th className="px-6 py-4">Route</th>
                <th className="px-6 py-4">LF %</th>
                <th className="px-6 py-4">Revenue Status</th>
                <th className="px-6 py-4">Risk Level</th>
                <th className="px-6 py-4">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant">
              {/* Row 1 */}
              <tr className="hover:bg-surface-container-lowest transition-colors text-sm">
                <td className="px-6 py-4 font-bold text-primary">SE1-2405</td>
                <td className="px-6 py-4 text-on-surface-variant">24 May, 06:00</td>
                <td className="px-6 py-4">HN - SG</td>
                <td className="px-6 py-4 font-semibold">96%</td>
                <td className="px-6 py-4">
                  <span className="text-green-600 font-bold">$42,200</span>
                </td>
                <td className="px-6 py-4">
                  <span className="px-2.5 py-1 bg-red-100 text-red-700 text-[10px] font-bold rounded uppercase">
                    High (Overbooked)
                  </span>
                </td>
                <td className="px-6 py-4">
                  <button className="p-1.5 rounded hover:bg-surface-container-high transition-colors">
                    <span className="material-symbols-outlined text-outline">more_vert</span>
                  </button>
                </td>
              </tr>
              {/* Row 2 */}
              <tr className="hover:bg-surface-container-lowest transition-colors text-sm">
                <td className="px-6 py-4 font-bold text-primary">SE3-2405</td>
                <td className="px-6 py-4 text-on-surface-variant">24 May, 22:15</td>
                <td className="px-6 py-4">HN - Vinh</td>
                <td className="px-6 py-4 font-semibold">42%</td>
                <td className="px-6 py-4">
                  <span className="text-red-600 font-bold">$8,450</span>
                </td>
                <td className="px-6 py-4">
                  <span className="px-2.5 py-1 bg-orange-100 text-orange-700 text-[10px] font-bold rounded uppercase">
                    Medium (Low Yield)
                  </span>
                </td>
                <td className="px-6 py-4">
                  <button className="p-1.5 rounded hover:bg-surface-container-high transition-colors">
                    <span className="material-symbols-outlined text-outline">more_vert</span>
                  </button>
                </td>
              </tr>
              {/* Row 3 */}
              <tr className="hover:bg-surface-container-lowest transition-colors text-sm">
                <td className="px-6 py-4 font-bold text-primary">SE2-2405</td>
                <td className="px-6 py-4 text-on-surface-variant">24 May, 19:30</td>
                <td className="px-6 py-4">SG - HN</td>
                <td className="px-6 py-4 font-semibold">71%</td>
                <td className="px-6 py-4">
                  <span className="text-on-surface font-bold">$29,100</span>
                </td>
                <td className="px-6 py-4">
                  <span className="px-2.5 py-1 bg-surface-container-highest text-on-surface-variant text-[10px] font-bold rounded uppercase">
                    Stable
                  </span>
                </td>
                <td className="px-6 py-4">
                  <button className="p-1.5 rounded hover:bg-surface-container-high transition-colors">
                    <span className="material-symbols-outlined text-outline">more_vert</span>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
