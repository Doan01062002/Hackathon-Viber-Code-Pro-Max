"use client";

import React from "react";
import { auditLogs } from "@/features/rail-ui/mockData";

export function AuditScreen() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-black text-on-surface">
          System Audit Trail
        </h2>
        <p className="text-sm text-on-surface-variant">
          Complete history of quota updates, override actions, and engine rules modifications
        </p>
      </div>

      {/* Main Table */}
      <div className="bg-white border border-outline-variant rounded-xl overflow-hidden shadow-sm">
        <div className="p-6 border-b border-outline-variant flex justify-between items-center bg-white">
          <h3 className="font-bold text-on-surface">Audit Logs</h3>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-outline text-sm">search</span>
            <input
              className="pl-10 pr-4 py-1.5 bg-surface-container-low border border-outline-variant rounded-full text-xs w-64 focus:ring-1 focus:ring-primary focus:outline-none"
              placeholder="Search audit trail..."
              type="text"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-surface-container-low text-xs text-on-surface-variant font-bold uppercase">
              <tr>
                <th className="px-6 py-4">Actor</th>
                <th className="px-6 py-4">Action</th>
                <th className="px-6 py-4">Entity</th>
                <th className="px-6 py-4 text-right">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/30 text-sm">
              {auditLogs.map((item) => (
                <tr className="hover:bg-surface-container-low transition-colors" key={`${item.actor}-${item.time}`}>
                  <td className="px-6 py-4 font-bold text-primary">{item.actor}</td>
                  <td className="px-6 py-4 text-on-surface font-semibold">{item.action}</td>
                  <td className="px-6 py-4 text-on-surface-variant font-medium">{item.entity}</td>
                  <td className="px-6 py-4 text-right text-on-surface-variant font-mono font-medium">{item.time}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
