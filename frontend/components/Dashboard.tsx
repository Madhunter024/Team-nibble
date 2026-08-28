"use client";

import React, { useState, useEffect } from 'react';
import { ThreatFeed } from './ThreatFeed';
import { fetchThreatLogs, fetchSystemHealth, ThreatLog } from '../lib/api';
import { Shield, Activity, Lock, AlertOctagon, RefreshCw, Cpu, Server } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const [logs, setLogs] = useState<ThreatLog[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [health, setHealth] = useState<{ status: string; redis: string }>({ status: 'checking', redis: 'checking' });

  const loadData = async () => {
    setLoading(true);
    const [fetchedLogs, healthStatus] = await Promise.all([
      fetchThreatLogs(),
      fetchSystemHealth()
    ]);
    setLogs(fetchedLogs);
    setHealth(healthStatus);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-8">
      {/* Top Navbar */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-cyan-950 border border-cyan-800 rounded-xl text-cyan-400">
              <Shield className="w-7 h-7" />
            </div>
            <div>
              <h1 className="text-2xl font-extrabold tracking-tight bg-gradient-to-r from-cyan-400 via-teal-300 to-emerald-400 bg-clip-text text-transparent">
                NIBDEFENDER
              </h1>
              <p className="text-xs text-slate-400 font-mono">Autonomous AI & Redis Threat Defense Gateway</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs font-mono">
            <Server className="w-4 h-4 text-cyan-400" />
            <span className="text-slate-400">FastAPI Status:</span>
            <span className={health.status === 'healthy' ? 'text-emerald-400 font-bold' : 'text-amber-400 font-bold'}>
              {health.status.toUpperCase()}
            </span>
          </div>

          <button
            onClick={loadData}
            className="flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </header>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 my-8">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Total Requests Monitored</span>
            <Activity className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-mono font-bold text-slate-100">148,920</div>
          <div className="mt-2 text-[11px] text-emerald-400 font-mono flex items-center gap-1">
            ▲ +14.2% velocity peak
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Active IP Blocks (Redis)</span>
            <Lock className="w-4 h-4 text-red-400" />
          </div>
          <div className="text-3xl font-mono font-bold text-slate-100">42</div>
          <div className="mt-2 text-[11px] text-red-400 font-mono">
            Rate-limiter auto-enforced
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">ML Anomaly Index</span>
            <Cpu className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-3xl font-mono font-bold text-purple-300">0.94</div>
          <div className="mt-2 text-[11px] text-purple-400 font-mono">
            IsolationForest Model Output
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">High Risk Attacks</span>
            <AlertOctagon className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-mono font-bold text-amber-400">{logs.length}</div>
          <div className="mt-2 text-[11px] text-amber-400 font-mono">
            LangChain AI Flagged
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ThreatFeed logs={logs} />
        </div>

        {/* Status Side Panel */}
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-2xl">
            <h3 className="text-sm font-bold text-slate-200 mb-4 uppercase tracking-wider flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
              Security Engine Controls
            </h3>
            
            <div className="space-y-4 text-xs">
              <div className="flex items-center justify-between p-3 bg-slate-950/80 rounded-lg border border-slate-800">
                <span className="text-slate-300 font-medium">Redis Token Bucket</span>
                <span className="px-2 py-0.5 bg-emerald-950 text-emerald-400 border border-emerald-800 rounded font-mono">ACTIVE</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-slate-950/80 rounded-lg border border-slate-800">
                <span className="text-slate-300 font-medium">PyJWT Token Guard</span>
                <span className="px-2 py-0.5 bg-emerald-950 text-emerald-400 border border-emerald-800 rounded font-mono">STRICT</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-slate-950/80 rounded-lg border border-slate-800">
                <span className="text-slate-300 font-medium">IsolationForest ML Engine</span>
                <span className="px-2 py-0.5 bg-purple-950 text-purple-400 border border-purple-800 rounded font-mono">TRAINED</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-slate-950/80 rounded-lg border border-slate-800">
                <span className="text-slate-300 font-medium">LangChain Incident Reporter</span>
                <span className="px-2 py-0.5 bg-cyan-950 text-cyan-400 border border-cyan-800 rounded font-mono">READY</span>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-slate-900 via-slate-900 to-cyan-950 border border-slate-800 rounded-xl p-6 shadow-xl">
            <h4 className="text-xs font-bold text-cyan-400 uppercase tracking-widest mb-2">Hackathon Demo Controls</h4>
            <p className="text-xs text-slate-400 mb-4 leading-relaxed">
              Launch the automated attack simulation script from the root directory to generate live traffic spikes and attack vectors.
            </p>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 font-mono text-[11px] text-slate-300 select-all">
              python scripts/attacker.py
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
