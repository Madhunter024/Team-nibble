"use client";

import React, { useState, useMemo } from 'react';
import { Search, Copy, Check, ShieldCheck } from 'lucide-react';

interface BlockedIPsTableProps {
  blockedIps: string[];
  onUnblock?: (ip: string) => void;
}

const getIpDetails = (ip: string) => {
  if (ip.startsWith("185.") || ip.startsWith("194.")) {
    return { reason: "SQL Injection Vectors", time: "10m ago" };
  }
  if (ip.startsWith("45.") || ip.startsWith("91.")) {
    return { reason: "Rate Flood (>100 req/s)", time: "25m ago" };
  }
  if (ip.startsWith("103.") || ip.startsWith("193.")) {
    return { reason: "JWT Signature Tampering", time: "1h ago" };
  }
  return { reason: "WAF Anomaly & Bot Probe", time: "2m ago" };
};

export const BlockedIPsTable: React.FC<BlockedIPsTableProps> = ({ blockedIps = [], onUnblock }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [copiedIp, setCopiedIp] = useState<string | null>(null);
  const [unblockedSet, setUnblockedSet] = useState<Set<string>>(new Set());
  const [manualIpInput, setManualIpInput] = useState('');
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);

  const handleCopy = (ip: string) => {
    navigator.clipboard.writeText(ip);
    setCopiedIp(ip);
    setTimeout(() => setCopiedIp(null), 2000);
  };

  const handleUnblock = (ip: string) => {
    const cleanIp = ip.trim();
    if (!cleanIp) return;
    setUnblockedSet((prev) => new Set(prev).add(cleanIp));
    if (onUnblock) {
      onUnblock(cleanIp);
    }
  };

  const handleManualUnblockSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const cleanIp = manualIpInput.trim();
    if (!cleanIp) return;

    handleUnblock(cleanIp);
    setManualIpInput('');
    setFeedbackMsg(`IP ${cleanIp} unblocked successfully`);
    setTimeout(() => setFeedbackMsg(null), 3000);
  };

  const activeBlockedIps = useMemo(() => {
    return blockedIps.filter((ip) => !unblockedSet.has(ip));
  }, [blockedIps, unblockedSet]);

  const filteredIps = useMemo(() => {
    return activeBlockedIps.filter((ip) => ip.includes(searchQuery.trim()));
  }, [activeBlockedIps, searchQuery]);

  return (
    <div className="glass-panel p-6 shadow-sm flex flex-col h-[500px]">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3.5 border-b border-white/[0.06]">
        <div>
          <h3 className="text-base font-semibold text-slate-100 tracking-tight">
            Blocked Sources
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            {activeBlockedIps.length} malicious addresses isolated
          </p>
        </div>

        <div className="text-xs text-slate-400 font-mono">
          Enforced via Redis Token Bucket
        </div>
      </div>

      {/* Manual Unblock Feedback Notification */}
      {feedbackMsg && (
        <div className="mt-2.5 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-xs text-emerald-400 font-mono animate-fade-in">
          ✓ {feedbackMsg}
        </div>
      )}

      {/* Search Bar & Manual Unblock Input Form */}
      <div className="flex flex-col sm:flex-row gap-2 my-3">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search blacklisted IP..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-slate-950/60 border border-white/[0.06] rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-slate-700 transition"
          />
        </div>

        {/* Manual Unblock Input Form */}
        <form onSubmit={handleManualUnblockSubmit} className="flex gap-1.5">
          <input
            type="text"
            placeholder="Manual IP (e.g. 192.168.1.1)"
            value={manualIpInput}
            onChange={(e) => setManualIpInput(e.target.value)}
            className="w-44 px-2.5 py-1.5 bg-slate-950/60 border border-white/[0.06] rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500/50 transition font-mono"
          />
          <button
            type="submit"
            disabled={!manualIpInput.trim()}
            className="px-3 py-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-lg text-xs font-medium transition disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1 shrink-0"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            Unblock
          </button>
        </form>
      </div>

      {/* Table Container */}
      <div className="flex-1 overflow-x-auto overflow-y-auto custom-scrollbar border border-white/[0.04] rounded-xl bg-slate-950/30">
        <table className="w-full text-left text-xs">
          <thead className="sticky top-0 bg-slate-950/90 text-slate-400 font-medium text-[11px] uppercase border-b border-white/[0.06] z-10">
            <tr>
              <th className="py-2.5 px-3">IP Address</th>
              <th className="py-2.5 px-3">Threat</th>
              <th className="py-2.5 px-3">Status</th>
              <th className="py-2.5 px-3">Time</th>
              <th className="py-2.5 px-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04] text-slate-300">
            {filteredIps.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-12 text-center text-slate-500 text-xs font-mono">
                  {searchQuery ? "No IP addresses match search." : "No IP addresses currently blocked."}
                </td>
              </tr>
            ) : (
              filteredIps.map((ip) => {
                const details = getIpDetails(ip);
                return (
                  <tr key={ip} className="hover:bg-slate-900/40 transition-colors">
                    {/* IP */}
                    <td className="py-2.5 px-3 font-mono font-medium text-slate-200 whitespace-nowrap">
                      {ip}
                    </td>

                    {/* Threat */}
                    <td className="py-2.5 px-3 text-slate-300 max-w-[160px] truncate" title={details.reason}>
                      {details.reason}
                    </td>

                    {/* Status */}
                    <td className="py-2.5 px-3 whitespace-nowrap">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                        BLOCKED
                      </span>
                    </td>

                    {/* Time */}
                    <td className="py-2.5 px-3 text-slate-400 font-mono text-[11px] whitespace-nowrap">
                      {details.time}
                    </td>

                    {/* Actions */}
                    <td className="py-2.5 px-3 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => handleCopy(ip)}
                          className="p-1 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded transition"
                          title="Copy IP"
                        >
                          {copiedIp === ip ? (
                            <Check className="w-3.5 h-3.5 text-emerald-400" />
                          ) : (
                            <Copy className="w-3.5 h-3.5" />
                          )}
                        </button>
                        <button
                          onClick={() => handleUnblock(ip)}
                          className="px-2 py-0.5 hover:bg-slate-800 text-slate-400 hover:text-emerald-400 border border-white/[0.06] rounded transition text-[11px]"
                          title="Unblock IP"
                        >
                          Release
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
