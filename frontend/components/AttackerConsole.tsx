"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Terminal, Zap, ShieldAlert, Activity } from 'lucide-react';

interface LogEntry {
  id: string;
  timestamp: string;
  method: string;
  endpoint: string;
  status: number | string;
  response: string;
  type: 'clean' | 'attack' | 'ddos';
}

export const AttackerConsole: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isAttacking, setIsAttacking] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const addLog = (log: Omit<LogEntry, 'id' | 'timestamp'>) => {
    const newLog: LogEntry = {
      ...log,
      id: Math.random().toString(36).substring(2, 9),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 }),
    };
    setLogs((prev) => [...prev, newLog]);
  };

  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  const generateRandomIp = () => `185.220.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`;

  const handleCleanTraffic = async () => {
    const payload = { username: 'admin', password: 'secret123' };
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-Forwarded-For': generateRandomIp()
        },
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({}));
      addLog({
        method: 'POST',
        endpoint: '/api/v1/auth/login',
        status: res.status,
        response: res.status === 200 ? 'OK - Token Granted' : (res.status === 403 ? 'Forbidden - Quarantined' : JSON.stringify(data).substring(0, 40)),
        type: 'clean'
      });
    } catch (err: any) {
      addLog({ method: 'POST', endpoint: '/api/v1/auth/login', status: 'ERR', response: err.message, type: 'clean' });
    }
  };

  const handleSqlInjection = async () => {
    const payload = { username: "admin' OR 1=1 --", password: 'x' };
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-Forwarded-For': generateRandomIp()
        },
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({}));
      addLog({
        method: 'POST',
        endpoint: '/api/v1/auth/login',
        status: res.status,
        response: res.status === 403 ? 'Forbidden - Quarantined' : JSON.stringify(data).substring(0, 40),
        type: 'attack'
      });
    } catch (err: any) {
      addLog({ method: 'POST', endpoint: '/api/v1/auth/login', status: 'ERR', response: err.message, type: 'attack' });
    }
  };

  const handleDdosSpike = async () => {
    setIsAttacking(true);
    const spikeIp = generateRandomIp(); // Use one IP for the burst to trigger rate limit
    for (let i = 0; i < 120; i++) {
      setTimeout(async () => {
        try {
          const res = await fetch(`${API_URL}/api/v1/search?q=ddos`, {
            method: 'GET',
            headers: { 'X-Forwarded-For': spikeIp }
          });
          addLog({
            method: 'GET',
            endpoint: '/api/v1/search',
            status: res.status,
            response: res.status === 429 ? 'Too Many Requests' : (res.status === 403 ? 'Forbidden - Quarantined' : 'OK'),
            type: 'ddos'
          });
        } catch (err: any) {
          addLog({ method: 'GET', endpoint: '/api/v1/search', status: 'ERR', response: err.message, type: 'ddos' });
        }
      }, i * 20); // Fire every 20ms
    }
    setTimeout(() => setIsAttacking(false), 120 * 20 + 500);
  };

  const [customPayload, setCustomPayload] = useState("SELECT * FROM users WHERE '1'='1' --");
  const [customEndpoint, setCustomEndpoint] = useState("/api/v1/auth/login");

  const handleCustomAttack = async () => {
    try {
      const res = await fetch(`${API_URL}${customEndpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Forwarded-For': generateRandomIp()
        },
        body: JSON.stringify({ payload: customPayload, input: customPayload }),
      });
      const data = await res.json().catch(() => ({}));
      addLog({
        method: 'POST',
        endpoint: customEndpoint,
        status: res.status,
        response: res.status === 403 ? 'Forbidden - Local ML Quarantined' : (res.status === 429 ? 'Too Many Requests - Rate Limited' : JSON.stringify(data).substring(0, 45)),
        type: 'attack'
      });
    } catch (err: any) {
      addLog({ method: customEndpoint, endpoint: customEndpoint, status: 'ERR', response: err.message, type: 'attack' });
    }
  };

  return (
    <div className="flex flex-col h-full bg-zinc-950 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-zinc-900 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Terminal className="w-5 h-5 text-red-500" />
          <h2 className="text-sm font-bold text-slate-200 tracking-wide">Red-Team Traffic Generator</h2>
        </div>
        <div className="px-2 py-1 bg-red-950/30 border border-red-900/50 rounded text-[10px] font-mono text-red-400">
          TARGET: {API_URL}/api/v1/data
        </div>
      </div>

      {/* Controls */}
      <div className="p-4 bg-zinc-900/50 border-b border-slate-800 flex flex-col gap-3">
        <button
          onClick={handleCleanTraffic}
          className="flex items-center justify-center gap-2 w-full py-2 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg transition-colors border border-slate-700"
        >
          <Activity className="w-4 h-4 text-emerald-400" />
          Send Clean Traffic
        </button>
        <button
          onClick={handleSqlInjection}
          className="flex items-center justify-center gap-2 w-full py-2 px-4 bg-amber-950/50 hover:bg-amber-900/60 text-amber-500 text-sm font-medium rounded-lg transition-colors border border-amber-900/50"
        >
          <ShieldAlert className="w-4 h-4" />
          Execute SQL Injection
        </button>
        <button
          onClick={handleDdosSpike}
          disabled={isAttacking}
          className="flex items-center justify-center gap-2 w-full py-2 px-4 bg-red-950/50 hover:bg-red-900/60 disabled:opacity-50 text-red-500 text-sm font-medium rounded-lg transition-colors border border-red-900/50"
        >
          <Zap className="w-4 h-4" />
          {isAttacking ? 'Firing...' : 'Launch DDoS Spike'}
        </button>

        {/* Custom Attack Payload Lab */}
        <div className="mt-2 pt-3 border-t border-slate-800 flex flex-col gap-2">
          <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider font-semibold">
            Custom Attack Payload Lab:
          </div>
          <input
            type="text"
            value={customEndpoint}
            onChange={(e) => setCustomEndpoint(e.target.value)}
            placeholder="Target Endpoint e.g. /api/v1/auth/login"
            className="w-full px-3 py-1.5 bg-black border border-slate-800 rounded text-xs font-mono text-slate-300 focus:outline-none focus:border-red-900"
          />
          <input
            type="text"
            value={customPayload}
            onChange={(e) => setCustomPayload(e.target.value)}
            placeholder="Custom Payload e.g. <script>alert(1)</script>"
            className="w-full px-3 py-1.5 bg-black border border-slate-800 rounded text-xs font-mono text-amber-400 focus:outline-none focus:border-amber-900"
          />
          <button
            onClick={handleCustomAttack}
            className="w-full py-1.5 px-3 bg-purple-950/50 hover:bg-purple-900/60 text-purple-300 text-xs font-mono font-medium rounded border border-purple-800/40 transition-colors"
          >
            ⚡ Fire Custom Payload
          </button>
        </div>
      </div>

      {/* Terminal Output */}
      <div className="flex-1 p-4 overflow-y-auto bg-black font-mono text-xs leading-relaxed">
        {logs.length === 0 ? (
          <div className="text-zinc-600 italic">Waiting for command execution...</div>
        ) : (
          logs.map((log) => (
            <div key={log.id} className="mb-1 flex flex-col sm:flex-row sm:gap-2">
              <span className="text-zinc-500 shrink-0">[{log.timestamp}]</span>
              <span className="text-slate-300">
                <span className={log.type === 'clean' ? 'text-emerald-400' : log.type === 'attack' ? 'text-amber-400' : 'text-red-400'}>
                  {log.method}
                </span>{' '}
                {log.endpoint}
              </span>
              <span className="text-zinc-400 sm:ml-auto">
                <span className={log.status === 200 ? 'text-emerald-500' : (log.status === 403 || log.status === 400 || log.status === 429) ? 'text-red-500' : 'text-amber-500'}>
                  {log.status}
                </span>{' '}
                - {log.response}
              </span>
            </div>
          ))
        )}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
};
