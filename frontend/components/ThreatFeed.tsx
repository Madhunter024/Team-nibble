"use client";

import React from 'react';
import { ThreatLog } from '../lib/api';
import { ShieldAlert, ShieldX, AlertTriangle, Cpu, Terminal } from 'lucide-react';

interface ThreatFeedProps {
  logs: ThreatLog[];
}

export const ThreatFeed: React.FC<ThreatFeedProps> = ({ logs }) => {
  const getSeverityBadge = (severity: ThreatLog['severity']) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-red-900/60 text-red-300 border-red-700/50';
      case 'HIGH':
        return 'bg-orange-900/60 text-orange-300 border-orange-700/50';
      case 'MEDIUM':
        return 'bg-yellow-900/60 text-yellow-300 border-yellow-700/50';
      default:
        return 'bg-blue-900/60 text-blue-300 border-blue-700/50';
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-2xl flex flex-col h-[520px]">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-red-950/80 border border-red-800/60 rounded-lg text-red-400 animate-pulse">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              Live Threat Feed & AI Incident Log
            </h2>
            <p className="text-xs text-slate-400">Powered by LangChain & OpenAI Incident Intelligence</p>
          </div>
        </div>
        <span className="flex items-center gap-1.5 px-3 py-1 bg-emerald-950/80 border border-emerald-800/60 text-emerald-400 text-xs font-mono rounded-full">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
          REALTIME MONITORED
        </span>
      </div>

      {/* Scrolling Container */}
      <div className="flex-1 overflow-y-auto mt-4 pr-1 space-y-3 custom-scrollbar">
        {logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500 gap-2">
            <Terminal className="w-8 h-8 stroke-1 text-slate-600" />
            <p className="text-sm">No security incidents flagged in active window.</p>
          </div>
        ) : (
          logs.map((log) => (
            <div
              key={log.id}
              className="bg-slate-950/70 border border-slate-800/90 rounded-lg p-4 transition-all hover:border-slate-700 hover:bg-slate-950"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${getSeverityBadge(log.severity)}`}>
                    {log.severity}
                  </span>
                  <span className="font-mono text-xs text-slate-300 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                    IP: {log.ip}
                  </span>
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    {log.threatType}
                  </span>
                </div>
                <span className="text-[11px] font-mono text-slate-500">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
              </div>

              <div className="flex items-start gap-2 mt-2 text-xs text-slate-300 leading-relaxed bg-slate-900/60 p-2.5 rounded border border-slate-800/60">
                <Cpu className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                <p><strong className="text-cyan-400">AI Report:</strong> {log.aiSummary}</p>
              </div>

              <div className="flex justify-end gap-2 mt-3 pt-2 border-t border-slate-900">
                <button className="px-3 py-1 bg-red-950/90 hover:bg-red-900 border border-red-800/60 text-red-300 text-xs font-medium rounded transition">
                  Enforce IP Ban
                </button>
                <button className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded transition">
                  View Payload Diffs
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
