"use client";

import React from "react";
import { alerts } from "@/features/rail-ui/mockData";

export function AlertsScreen() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-black text-on-surface">
          System Alerts & Warnings
        </h2>
        <p className="text-sm text-on-surface-variant">
          Real-time capacity bottlenecks, quota alerts, and yield warning signals
        </p>
      </div>

      {/* Alerts List */}
      <div className="space-y-4">
        {alerts.map((alert) => {
          const isHigh = alert.severity === "Cao";
          return (
            <div
              key={alert.title}
              className={`p-5 rounded-xl border flex justify-between items-start gap-4 transition-colors duration-200 ${
                isHigh
                  ? "bg-error-container/10 border-error/20 hover:bg-error-container/20"
                  : "bg-surface border-outline-variant hover:bg-surface-container-low"
              }`}
            >
              <div className="flex gap-4">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                    isHigh ? "bg-error text-white" : "bg-secondary text-white"
                  }`}
                >
                  <span className="material-symbols-outlined text-base">
                    {isHigh ? "warning" : "info"}
                  </span>
                </div>
                <div>
                  <p className={`font-bold text-sm ${isHigh ? "text-error" : "text-on-surface"}`}>
                    {alert.title}
                  </p>
                  <p className="text-xs text-on-surface-variant font-semibold mt-1 leading-relaxed">
                    {alert.detail}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <span
                  className={`px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                    isHigh ? "bg-error/15 text-error" : "bg-secondary-container text-on-secondary-container"
                  }`}
                >
                  {alert.severity}
                </span>
                <button className="px-3 py-1.5 border border-outline-variant rounded-md text-xs font-bold hover:bg-surface-container transition-colors text-on-surface">
                  Resolve
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
