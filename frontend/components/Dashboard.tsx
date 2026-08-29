"use client";

import React, { useState, useEffect } from 'react';
import { ThreatMetrics, TrafficDataPoint } from '../lib/mockData';
import { ApiResponseMeta } from '../lib/api';
import { TrafficChart } from './TrafficChart';
import { ThreatFeed } from './ThreatFeed';
import { BlockedIPsTable } from './BlockedIPsTable';
import {
  Shield,
  Activity,
  Lock,
  CheckCircle2,
  HelpCircle,
  RefreshCw,
  Server,
  Zap,
  Layers,
  Globe,
  Cpu,
  Sliders,
} from 'lucide-react';

interface DashboardProps {
  metrics: ThreatMetrics;
  meta?: ApiResponseMeta;
  trafficHistory?: TrafficDataPoint[];
  loading?: boolean;
  samplingRate?: number;
  onRefresh?: () => void;
  onUnblockIp?: (ip: string) => void;
  onSamplingRateChange?: (newRate: number) => void;
  onTriggerSimulatedAttack?: () => void;
}

const SAMPLING_OPTIONS = [
  { rate: 0.25, label: "25%", subtitle: "Max Efficiency", computeSaved: "75% Compute Saved" },
  { rate: 0.50, label: "50%", subtitle: "Balanced Mode", computeSaved: "50% Compute Saved" },
  { rate: 0.75, label: "75%", subtitle: "High Inspection", computeSaved: "25% Compute Saved" },
  { rate: 1.0, label: "100%", subtitle: "Full Inspection", computeSaved: "100% Monitored" },
];

export const Dashboard: React.FC<DashboardProps> = ({
  metrics,
  meta,
  trafficHistory = [],
  loading = false,
  samplingRate,
  onRefresh,
  onUnblockIp,
  onSamplingRateChange,
}) => {
  const [lastUpdatedTime, setLastUpdatedTime] = useState<string>('');
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null);
  const [isMounted, setIsMounted] = useState<boolean>(false);

  useEffect(() => {
    setIsMounted(true);
    const updateTime = () => {
      setLastUpdatedTime(
        new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const currentSamplingRate = samplingRate !== undefined ? samplingRate : (metrics.sampling_rate ?? 1.0);
  const isLive = meta ? !meta.isFallback : false;

  const securityControls = [
    {
      name: "Zero-Trust",
      status: "Enforced",
      icon: <Layers className="w-4 h-4 text-cyan-400" />,
      hint: "Every request is verified before access is granted.",
    },
    {
      name: "WAF",
      status: "Active",
      icon: <Globe className="w-4 h-4 text-emerald-400" />,
      hint: "Filters malicious web requests before they reach the application.",
    },
    {
      name: "AI Threat Detection",
      status: "Monitoring",
      icon: <Cpu className="w-4 h-4 text-indigo-400" />,
      hint: "Identifies unusual traffic patterns and potential attacks.",
    },
    {
      name: "Rate Limiting",
      status: "Enabled",
      icon: <Sliders className="w-4 h-4 text-teal-400" />,
      hint: "Controls excessive requests to reduce abuse.",
    },
  ];

  return (
    <div className="bg-[#080b11] text-slate-100 p-4 sm:p-6 lg:p-8 ambient-bg selection:bg-cyan-500 selection:text-slate-950 h-full">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* ========================================================= */}
        {/* 1. HEADER */}
        {/* ========================================================= */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-white/[0.06]">
          {/* Logo & Title */}
          <div className="flex items-center gap-3.5">
            <div className="p-2.5 bg-cyan-950/40 border border-cyan-500/20 rounded-xl text-cyan-400">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight text-white">
                  NibDefender
                </h1>
                <span className="text-slate-500 text-xs">•</span>
                <span className="text-sm font-medium text-slate-200">
                  Security Operations
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Real-time threat visibility
              </p>
            </div>
          </div>

          {/* System Status Indicator & Metadata */}
          <div className="flex flex-wrap items-center gap-3 text-xs">
            {/* Status Pill */}
            <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-full">
              <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block animate-pulse"></span>
              <span className="font-semibold text-xs tracking-wide">Protected</span>
            </div>

            {/* Backend connection indicator */}
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900/60 border border-white/[0.06] rounded-lg text-slate-400 font-mono text-[11px]">
              <Server className="w-3.5 h-3.5 text-slate-500" />
              <span>{isLive ? 'Backend: Live' : 'Backend: Fallback (Sim)'}</span>
            </div>

            {/* Last updated timestamp */}
            <div className="text-slate-400 font-mono text-[11px] px-2.5 py-1.5 bg-slate-950/60 rounded-lg border border-white/[0.06]">
              Last updated:{' '}
              <span suppressHydrationWarning>
                {isMounted && lastUpdatedTime ? lastUpdatedTime : 'Just now'}
              </span>
            </div>

            {/* Refresh button */}
            {onRefresh && (
              <button
                onClick={onRefresh}
                className="p-1.5 bg-slate-900/60 hover:bg-slate-800 border border-white/[0.06] text-slate-400 hover:text-slate-200 rounded-lg transition"
                title="Poll now"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              </button>
            )}
          </div>
        </header>

        {/* ========================================================= */}
        {/* 2. KPI SECTION (3 Compact Cards with Circular Icons) */}
        {/* ========================================================= */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Card 1: Total Requests */}
          <div className="glass-panel p-5 shadow-sm hover:border-white/[0.12] transition-all flex items-center justify-between">
            <div>
              <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">
                Total Requests
              </div>
              <div className="text-2xl sm:text-3xl font-bold font-mono text-slate-100 tracking-tight">
                {metrics.total_requests.toLocaleString()}
              </div>
              <div className="mt-1 text-xs text-slate-400">
                Processed in real time
              </div>
            </div>

            {/* Circular Icon Container */}
            <div className="w-12 h-12 rounded-full bg-cyan-950/50 border border-cyan-500/20 flex items-center justify-center text-cyan-400 shrink-0 ml-4">
              <Activity className="w-5 h-5" />
            </div>
          </div>

          {/* Card 2: Threats Blocked */}
          <div className="glass-panel p-5 shadow-sm hover:border-white/[0.12] transition-all flex items-center justify-between">
            <div>
              <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">
                Threats Blocked
              </div>
              <div className="text-2xl sm:text-3xl font-bold font-mono text-slate-100 tracking-tight">
                {metrics.blocked_ips_count}
              </div>
              <div className="mt-1 text-xs text-slate-400">
                Active malicious sources
              </div>
            </div>

            {/* Circular Icon Container */}
            <div className="w-12 h-12 rounded-full bg-rose-950/50 border border-rose-500/20 flex items-center justify-center text-rose-400 shrink-0 ml-4">
              <Lock className="w-5 h-5" />
            </div>
          </div>

          {/* Card 3: System Status */}
          <div className="glass-panel p-5 shadow-sm hover:border-white/[0.12] transition-all flex items-center justify-between">
            <div>
              <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">
                System Status
              </div>
              <div className="text-2xl sm:text-3xl font-bold text-emerald-400 tracking-tight">
                Protected
              </div>
              <div className="mt-1 text-xs text-slate-400">
                Zero-Trust Active
              </div>
            </div>

            {/* Circular Icon Container */}
            <div className="w-12 h-12 rounded-full bg-emerald-950/50 border border-emerald-500/20 flex items-center justify-center text-emerald-400 shrink-0 ml-4">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>
        </section>

        {/* ========================================================= */}
        {/* EXECUTIVE AI THREAT CARD */}
        {/* ========================================================= */}
        {metrics.recent_alerts && metrics.recent_alerts.length > 0 && metrics.recent_alerts[0].severity === 'HIGH' && (
          <section className="relative overflow-hidden rounded-xl bg-slate-900/40 border border-indigo-500/30 p-1">
            <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-cyan-500/10 blur-xl"></div>
            <div className="relative bg-slate-950/80 backdrop-blur-sm p-5 rounded-lg border border-white/5 flex flex-col gap-3">
              <div className="flex items-center gap-2">
                <div className="p-1.5 bg-indigo-500/20 rounded-md">
                  <Zap className="w-4 h-4 text-indigo-400" />
                </div>
                <h3 className="text-sm font-bold text-indigo-300 tracking-wide uppercase">AI Threat Analysis (Local Scikit-Learn ML)</h3>
                <span className="ml-auto flex h-2 w-2 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
                </span>
              </div>
              <p className="text-sm text-slate-300 leading-relaxed font-mono">
                {metrics.recent_alerts[0].message}
              </p>
            </div>
          </section>
        )}

        {/* ========================================================= */}
        {/* 2.5. API TRAFFIC SAMPLING OPTIONS */}
        {/* ========================================================= */}
        <section className="glass-panel p-5 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3.5 border-b border-white/[0.06]">
            <div className="flex items-center gap-2.5">
              <div className="p-2 bg-indigo-950/50 border border-indigo-500/20 rounded-lg text-indigo-400">
                <Sliders className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-100 tracking-tight">
                  API Traffic Sampling Rate
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Choose the ML anomaly detection sampling of the API
                </p>
              </div>
            </div>

            {/* Current Active Badge */}
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono text-slate-400">Active Rate:</span>
              <span className="px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
                {Math.round(currentSamplingRate * 100)}% Sampling
              </span>
            </div>
          </div>

          {/* Sampling Option Buttons: 20%, 40%, 50%, 100% */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
            {SAMPLING_OPTIONS.map((opt) => {
              const isSelected = Math.round(currentSamplingRate * 100) === Math.round(opt.rate * 100);
              return (
                <button
                  key={opt.label}
                  type="button"
                  onClick={() => onSamplingRateChange && onSamplingRateChange(opt.rate)}
                  className={`p-3.5 rounded-xl border text-left transition-all duration-200 cursor-pointer ${
                    isSelected
                      ? 'bg-gradient-to-br from-cyan-950/80 via-slate-900 to-slate-900 border-cyan-400/70 shadow-[0_0_16px_rgba(6,182,212,0.25)] text-white ring-1 ring-cyan-400/50'
                      : 'bg-slate-950/60 hover:bg-slate-900/80 border-white/[0.08] hover:border-white/[0.18] text-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-lg font-bold font-mono tracking-tight text-white">
                      {opt.label}
                    </span>
                    {isSelected && (
                      <span className="flex h-2.5 w-2.5 relative">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-cyan-400"></span>
                      </span>
                    )}
                  </div>
                  <div className="text-xs font-medium text-slate-200 mt-1.5">
                    {opt.subtitle}
                  </div>
                  <div className={`text-[10px] font-mono mt-0.5 ${isSelected ? 'text-cyan-300 font-semibold' : 'text-slate-400'}`}>
                    {opt.computeSaved}
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        {/* ========================================================= */}
        {/* 3. TRAFFIC SECTION */}
        {/* ========================================================= */}
        <section>
          <TrafficChart data={trafficHistory} />
        </section>

        {/* ========================================================= */}
        {/* 4 & 5. RECENT THREATS & BLOCKED SOURCES */}
        {/* ========================================================= */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Threats Feed */}
          <ThreatFeed alerts={metrics.recent_alerts} />

          {/* Blocked Sources Table */}
          <BlockedIPsTable
            blockedIps={metrics.blocked_ips_list}
            onUnblock={onUnblockIp}
          />
        </section>

        {/* ========================================================= */}
        {/* 6 & 7. SECURITY CONTROLS & CYBERSECURITY HINTS */}
        {/* ========================================================= */}
        <section className="glass-panel p-5 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Security Controls
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Active automated defense layers
              </p>
            </div>

            {/* Control Badges with Tooltips */}
            <div className="flex flex-wrap items-center gap-2.5 sm:gap-3">
              {securityControls.map((control) => (
                <div
                  key={control.name}
                  className="relative group flex items-center gap-2 px-3 py-1.5 bg-slate-950/50 border border-white/[0.06] rounded-xl text-xs"
                >
                  <span className="text-emerald-400 font-bold">✓</span>
                  {control.icon}
                  <span className="text-slate-200 font-medium">{control.name}</span>
                  <span className="text-[10px] text-slate-400 font-mono">({control.status})</span>

                  {/* Info Icon with Accessible Tooltip */}
                  <button
                    type="button"
                    onClick={() => setActiveTooltip(activeTooltip === control.name ? null : control.name)}
                    className="text-slate-500 hover:text-slate-300 ml-0.5 focus:outline-none"
                    aria-label={`Info for ${control.name}`}
                  >
                    <HelpCircle className="w-3.5 h-3.5" />
                  </button>

                  {/* Tooltip Card */}
                  <div
                    className={`absolute bottom-full mb-2 left-1/2 -translate-x-1/2 w-52 p-2.5 bg-slate-900 text-slate-200 text-[11px] rounded-xl shadow-2xl border border-slate-700 pointer-events-none transition-all z-20 leading-relaxed ${
                      activeTooltip === control.name ? 'opacity-100 visible' : 'opacity-0 invisible group-hover:opacity-100 group-hover:visible'
                    }`}
                  >
                    {control.hint}
                    <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-900"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

      </div>
    </div>
  );
};
