"use client";

import React from "react";

export function SimulationScreen() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-3xl font-black text-on-surface">
            Impact Simulation & Verification
          </h2>
          <p className="text-sm text-on-surface-variant">
            Simulate and verify the yield impact of adjusted pricing strategies before system deployment
          </p>
        </div>
      </div>

      {/* Main Simulation Panel */}
      <div className="bg-white border border-outline-variant rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-8 border-b border-outline-variant/30 pb-4">
          <div>
            <h3 className="font-bold text-base flex items-center gap-2 text-on-surface">
              <span className="material-symbols-outlined text-primary">analytics</span>
              Impact Simulation Panel
            </h3>
            <p className="text-xs text-on-surface-variant font-medium mt-0.5">
              Comparison of current metrics vs. simulated recommendations
            </p>
          </div>
          <div className="flex items-center gap-2 text-[10px] font-bold bg-surface-container-low px-3 py-1.5 rounded-lg border border-outline-variant/30">
            <span className="w-2.5 h-2.5 rounded-full bg-primary" />
            <span className="text-on-surface-variant font-semibold">Current</span>
            <span className="w-2.5 h-2.5 rounded-full bg-secondary-container border border-primary ml-2" />
            <span className="text-on-surface-variant font-semibold">Simulated</span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Simulated Charts via CSS */}
          <div className="h-56 relative border-l-2 border-b-2 border-outline-variant flex items-end px-4 pb-2 gap-8">
            <div className="flex-1 flex flex-col items-center justify-end group">
              <div className="w-full flex items-end gap-2 px-6">
                <div className="bg-primary/20 w-full h-32 rounded-t transition-all group-hover:h-36" />
                <div className="bg-primary w-full h-44 rounded-t transition-all group-hover:h-48" />
              </div>
              <p className="mt-3 text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">
                Revenue (MM)
              </p>
              <p className="text-xs font-bold text-primary mt-1">+12.4% Est.</p>
            </div>

            <div className="flex-1 flex flex-col items-center justify-end group">
              <div className="w-full flex items-end gap-2 px-6">
                <div className="bg-secondary/20 w-full h-28 rounded-t transition-all group-hover:h-32" />
                <div className="bg-secondary w-full h-24 rounded-t transition-all group-hover:h-20" />
              </div>
              <p className="mt-3 text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">
                Load Factor
              </p>
              <p className="text-xs font-bold text-secondary mt-1">-4.2% Optimization</p>
            </div>

            {/* Grid Line Overlays */}
            <div className="absolute inset-0 pointer-events-none flex flex-col justify-between py-4 pl-[-20px] opacity-10">
              <span className="border-t border-dashed border-black w-full" />
              <span className="border-t border-dashed border-black w-full" />
              <span className="border-t border-dashed border-black w-full" />
            </div>
          </div>

          {/* AI Insights & Actions */}
          <div className="flex flex-col justify-center space-y-4">
            <div className="bg-surface-container-low p-5 rounded-xl border border-primary/20 relative overflow-hidden">
              <div className="absolute top-0 left-0 w-1 h-full bg-primary" />
              <p className="text-[10px] font-bold text-primary mb-2 uppercase tracking-wider">
                AI System Insight
              </p>
              <p className="text-sm leading-relaxed text-on-surface-variant font-medium">
                Accepting all pricing recommendations will result in an estimated yield increase of{" "}
                <span className="font-bold text-primary">€1.2M</span> over the next 14 days, primarily driven by peak Friday departures.
              </p>
            </div>

            <div className="flex gap-4">
              <button className="flex-1 py-3.5 bg-primary text-white rounded-lg font-bold text-sm hover:shadow-lg transition-all scale-100 hover:scale-[1.01] active:scale-95">
                Execute All Suggestions
              </button>
              <button className="px-6 py-3.5 border border-outline-variant rounded-lg font-bold text-sm hover:bg-surface-container transition-all text-on-surface">
                Fine Tune
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
