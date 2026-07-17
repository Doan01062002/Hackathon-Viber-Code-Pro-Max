"use client";

import React, { useState } from "react";

export function QuoteScreen() {
  const [strategy, setStrategy] = useState("revenue");

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-3xl font-black text-on-surface">
          Dynamic Pricing Control
        </h2>
        <p className="text-sm text-on-surface-variant font-medium">
          Manage pricing thresholds, strategy constraints, and active bottleneck pricing adjustments
        </p>
      </div>

      {/* Alerts Banner */}
      <div className="flex gap-4 overflow-x-auto pb-2 custom-scrollbar">
        <div className="flex-shrink-0 flex items-center gap-3 bg-error-container/30 border border-error/20 p-4 rounded-xl min-w-[320px]">
          <div className="w-10 h-10 rounded-full bg-error flex items-center justify-center text-white">
            <span className="material-symbols-outlined text-base">warning</span>
          </div>
          <div>
            <p className="font-bold text-sm text-error">Bottleneck: Leg LDN-MAN</p>
            <p className="text-xs text-on-error-container font-semibold">
              Load factor at 96%. Suggest +15% price shift.
            </p>
          </div>
        </div>

        <div className="flex-shrink-0 flex items-center gap-3 bg-primary-container/10 border border-primary/20 p-4 rounded-xl min-w-[320px]">
          <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center text-white">
            <span className="material-symbols-outlined text-base">bolt</span>
          </div>
          <div>
            <p className="font-bold text-sm text-primary">Opportunity: PAR-LYO</p>
            <p className="text-xs text-primary/80 font-semibold">
              Competitor outage detected. Optimize yield.
            </p>
          </div>
        </div>

        <div className="flex-shrink-0 flex items-center gap-3 bg-secondary-container/30 border border-secondary/20 p-4 rounded-xl min-w-[320px]">
          <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center text-white">
            <span className="material-symbols-outlined text-base">trending_down</span>
          </div>
          <div>
            <p className="font-bold text-sm text-secondary">Low Demand: MAD-BAR</p>
            <p className="text-xs text-on-secondary-container font-semibold">
              Price ceiling holding too high. Soften -8%.
            </p>
          </div>
        </div>
      </div>

      {/* Main Pricing Layout */}
      <div className="grid grid-cols-12 gap-6">
        {/* Pricing Control Center (Left side) */}
        <section className="col-span-12 lg:col-span-8 space-y-6">
          <div className="bg-white border border-outline-variant rounded-xl overflow-hidden shadow-sm">
            <div className="p-6 border-b border-outline-variant flex justify-between items-center">
              <div>
                <h3 className="text-base font-bold text-on-surface">Pricing Control Center</h3>
                <p className="text-xs text-on-surface-variant font-semibold mt-0.5">
                  OD (Origin-Destination) Pair Recommendations
                </p>
              </div>
              <div className="flex gap-2">
                <button className="px-3 py-1.5 border border-outline-variant rounded-md text-xs font-bold hover:bg-surface-container transition-colors">
                  Export CSV
                </button>
                <button className="px-3 py-1.5 bg-primary text-white rounded-md text-xs font-bold hover:brightness-110 transition-all">
                  Accept All Suggestions
                </button>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-surface-container-low text-xs text-on-surface-variant font-bold">
                  <tr>
                    <th className="px-6 py-4">OD Pair / Service</th>
                    <th className="px-6 py-4 text-center">Current</th>
                    <th className="px-6 py-4 text-center">AI Suggest</th>
                    <th className="px-6 py-4">Opportunity Cost (Bid Price)</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-outline-variant/30 text-sm">
                  {/* Row 1 */}
                  <tr className="hover:bg-surface-container-low transition-colors">
                    <td className="px-6 py-5">
                      <p className="font-bold text-on-surface">London ↔ Manchester</p>
                      <p className="text-xs text-on-surface-variant font-medium">S-Class High Speed</p>
                    </td>
                    <td className="px-6 py-5 text-center font-bold">£84.50</td>
                    <td className="px-6 py-5 text-center">
                      <span className="bg-primary/10 text-primary px-2.5 py-1 rounded font-bold">£98.00</span>
                    </td>
                    <td className="px-6 py-5">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-surface-container rounded-full overflow-hidden">
                          <div className="h-full bg-primary" style={{ width: "85%" }} />
                        </div>
                        <span className="text-xs font-bold text-primary">£112.40</span>
                      </div>
                      <p className="text-[10px] text-on-surface-variant mt-1 font-semibold">
                        Leg saturation at 92% capacity
                      </p>
                    </td>
                    <td className="px-6 py-5">
                      <span className="inline-flex items-center gap-1.5 bg-error/10 text-error px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider">
                        <span className="w-1.5 h-1.5 rounded-full bg-error animate-pulse" />
                        High Bottleneck
                      </span>
                    </td>
                    <td className="px-6 py-5 text-right">
                      <button className="material-symbols-outlined text-on-surface-variant hover:text-primary transition-colors">
                        more_vert
                      </button>
                    </td>
                  </tr>

                  {/* Row 2 */}
                  <tr className="hover:bg-surface-container-low transition-colors">
                    <td className="px-6 py-5">
                      <p className="font-bold text-on-surface">Paris ↔ Lyon</p>
                      <p className="text-xs text-on-surface-variant font-medium">TGV Direct</p>
                    </td>
                    <td className="px-6 py-5 text-center font-bold">€112.00</td>
                    <td className="px-6 py-5 text-center">
                      <span className="bg-primary/10 text-primary px-2.5 py-1 rounded font-bold">€118.50</span>
                    </td>
                    <td className="px-6 py-5">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-surface-container rounded-full overflow-hidden">
                          <div className="h-full bg-primary" style={{ width: "45%" }} />
                        </div>
                        <span className="text-xs font-bold text-primary">€124.00</span>
                      </div>
                      <p className="text-[10px] text-on-surface-variant mt-1 font-semibold">
                        Normal demand elasticity
                      </p>
                    </td>
                    <td className="px-6 py-5">
                      <span className="inline-flex items-center gap-1.5 bg-surface-container-highest text-on-surface-variant px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider">
                        <span className="w-1.5 h-1.5 rounded-full bg-on-surface-variant" />
                        Stable
                      </span>
                    </td>
                    <td className="px-6 py-5 text-right">
                      <button className="material-symbols-outlined text-on-surface-variant hover:text-primary transition-colors">
                        more_vert
                      </button>
                    </td>
                  </tr>

                  {/* Row 3 */}
                  <tr className="hover:bg-surface-container-low transition-colors">
                    <td className="px-6 py-5">
                      <p className="font-bold text-on-surface">Madrid ↔ Barcelona</p>
                      <p className="text-xs text-on-surface-variant font-medium">AVE Express</p>
                    </td>
                    <td className="px-6 py-5 text-center font-bold">€95.00</td>
                    <td className="px-6 py-5 text-center">
                      <span className="bg-tertiary-fixed-dim/30 text-tertiary-container px-2.5 py-1 rounded font-bold">€87.50</span>
                    </td>
                    <td className="px-6 py-5">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-surface-container rounded-full overflow-hidden">
                          <div className="h-full bg-tertiary-container" style={{ width: "20%" }} />
                        </div>
                        <span className="text-xs font-bold text-tertiary-container">€64.20</span>
                      </div>
                      <p className="text-[10px] text-on-surface-variant mt-1 font-semibold">
                        Low inventory utilization
                      </p>
                    </td>
                    <td className="px-6 py-5">
                      <span className="inline-flex items-center gap-1.5 bg-secondary-container/30 text-on-secondary-container px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider">
                        <span className="w-1.5 h-1.5 rounded-full bg-secondary" />
                        Underperforming
                      </span>
                    </td>
                    <td className="px-6 py-5 text-right">
                      <button className="material-symbols-outlined text-on-surface-variant hover:text-primary transition-colors">
                        more_vert
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Pricing Rule Engine (Right side) */}
        <aside className="col-span-12 lg:col-span-4 space-y-6">
          <div className="bg-surface-container-highest/50 border border-primary/10 rounded-xl p-6 glass-card shadow-sm">
            <div className="flex items-center gap-2 mb-6">
              <span className="material-symbols-outlined text-primary">rule_settings</span>
              <h3 className="font-bold text-base text-on-surface">Pricing Rule Engine</h3>
            </div>

            <div className="space-y-6">
              {/* Rule: Price Floor/Ceiling */}
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <label className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">
                    Price Range Constraint
                  </label>
                  <span className="material-symbols-outlined text-xs cursor-help">info</span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-white p-3 border border-outline-variant rounded-lg">
                    <p className="text-[10px] text-on-surface-variant mb-1 font-bold">Floor (Min)</p>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-on-surface-variant">€</span>
                      <input
                        className="border-none p-0 w-full font-bold focus:ring-0 text-sm bg-transparent outline-none"
                        type="text"
                        defaultValue="45.00"
                      />
                    </div>
                  </div>
                  <div className="bg-white p-3 border border-outline-variant rounded-lg">
                    <p className="text-[10px] text-on-surface-variant mb-1 font-bold">Ceiling (Max)</p>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-on-surface-variant">€</span>
                      <input
                        className="border-none p-0 w-full font-bold focus:ring-0 text-sm bg-transparent outline-none"
                        type="text"
                        defaultValue="450.00"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Rule: Delta Constraint */}
              <div className="space-y-3">
                <label className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">
                  Max Daily Delta (%)
                </label>
                <input
                  className="w-full accent-primary bg-surface-container h-2 rounded-full appearance-none cursor-pointer"
                  type="range"
                  min="5"
                  max="30"
                  defaultValue="15"
                />
                <div className="flex justify-between text-[10px] font-bold">
                  <span>5%</span>
                  <span className="text-primary">Current: 15%</span>
                  <span>30%</span>
                </div>
              </div>

              {/* Rule: Strategy Select */}
              <div className="space-y-3">
                <label className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">
                  Optimization Strategy
                </label>
                <div className="space-y-2">
                  <label
                    className={`flex items-center gap-3 p-3 bg-white border-2 rounded-lg cursor-pointer transition-all ${
                      strategy === "revenue" ? "border-primary" : "border-outline-variant"
                    }`}
                    onClick={() => setStrategy("revenue")}
                  >
                    <input
                      checked={strategy === "revenue"}
                      onChange={() => {}}
                      className="text-primary focus:ring-primary scale-90"
                      name="strategy"
                      type="radio"
                    />
                    <div>
                      <p className="text-xs font-bold text-on-surface">Revenue Maximizer</p>
                      <p className="text-[10px] text-on-surface-variant font-medium mt-0.5">
                        Prioritizes high-yield premium bookings
                      </p>
                    </div>
                  </label>

                  <label
                    className={`flex items-center gap-3 p-3 bg-white border rounded-lg cursor-pointer hover:bg-surface-container-low transition-all ${
                      strategy === "load" ? "border-primary border-2" : "border-outline-variant"
                    }`}
                    onClick={() => setStrategy("load")}
                  >
                    <input
                      checked={strategy === "load"}
                      onChange={() => {}}
                      className="text-primary focus:ring-primary scale-90"
                      name="strategy"
                      type="radio"
                    />
                    <div>
                      <p className="text-xs font-bold text-on-surface">Load Factor Filler</p>
                      <p className="text-[10px] text-on-surface-variant font-medium mt-0.5">
                        Aggressive pricing to fill empty seats
                      </p>
                    </div>
                  </label>

                  <label
                    className={`flex items-center gap-3 p-3 bg-white border rounded-lg cursor-pointer hover:bg-surface-container-low transition-all ${
                      strategy === "competitive" ? "border-primary border-2" : "border-outline-variant"
                    }`}
                    onClick={() => setStrategy("competitive")}
                  >
                    <input
                      checked={strategy === "competitive"}
                      onChange={() => {}}
                      className="text-primary focus:ring-primary scale-90"
                      name="strategy"
                      type="radio"
                    />
                    <div>
                      <p className="text-xs font-bold text-on-surface">Competitive Parity</p>
                      <p className="text-[10px] text-on-surface-variant font-medium mt-0.5">
                        Tracks competitor moves within 2% margin
                      </p>
                    </div>
                  </label>
                </div>
              </div>

              <button className="w-full py-3.5 bg-on-background text-white rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-black transition-all text-xs">
                <span className="material-symbols-outlined text-sm">published_with_changes</span>
                Update Engine Rules
              </button>
            </div>
          </div>

          {/* Contextual Map Component */}
          <div className="bg-white border border-outline-variant rounded-xl overflow-hidden shadow-sm h-64 relative group">
            <img
              className="w-full h-full object-cover"
              alt="Active Network Map"
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuDqefbziBtF-K_WFMPtQn5LoS4TRXshMSMORahY21cRunFCAS-YIGVYOapfQPJs_AVTnCAAOIvB4JmcTGxKcMvoE9inf24681pb8l_PTPzNQy4nHdsaxk1pqUGEPmMNBqoB-GPFiXrKkzMVVdYLW5m3wn-z7nzBhIAhzge2n5DIF_iPrLuB-6MTh-i4kpwtsfjRb529jgpp9l6kPZ3AZRilbpzO34_FLgDy--x43QtVqGi__FnW0G1pyd8X45cCLP7L-NmERI4PPWS2"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
            <div className="absolute bottom-4 left-4 text-white">
              <p className="text-[10px] font-bold uppercase tracking-widest opacity-80">
                Active Network Overlay
              </p>
              <p className="text-sm font-semibold">Monitoring 4 active bottlenecks</p>
            </div>
            <button className="absolute top-4 right-4 bg-white/20 backdrop-blur-md p-2 rounded-full text-white hover:bg-white/40 transition-all flex items-center justify-center">
              <span className="material-symbols-outlined text-sm">fullscreen</span>
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
}
