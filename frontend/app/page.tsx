"use client";

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Dashboard } from '../components/Dashboard';
import { AttackerConsole } from '../components/AttackerConsole';
import { fetchThreatMetrics, unblockIpOnBackend, updateSamplingConfig } from '../lib/api';
import {
  initialMockData,
  generateInitialTrafficHistory,
  TrafficDataPoint,
  ThreatMetrics,
  ThreatAlert,
  ApiResponseMeta,
} from '../lib/mockData';


export default function Home() {
  const [metrics, setMetrics] = useState<ThreatMetrics>(initialMockData);
  const [samplingRate, setSamplingRate] = useState<number>(1.0);
  const [meta, setMeta] = useState<ApiResponseMeta>({
    isFallback: true,
    timestamp: "2026-08-28T18:45:00.000Z",
    source: 'mock_simulation',
    latencyMs: 12,
  });
  const [trafficHistory, setTrafficHistory] = useState<TrafficDataPoint[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const isPollingRef = useRef<boolean>(false);

  // Initialize traffic history on first mount (client-side only to avoid hydration mismatch)
  useEffect(() => {
    setTrafficHistory(generateInitialTrafficHistory(15));
  }, []);

  // Poll function to fetch metrics every 2 seconds
  const pollData = useCallback(async (isManual = false) => {
    if (isPollingRef.current && !isManual) return;
    isPollingRef.current = true;
    if (isManual) setLoading(true);

    try {
      const response = await fetchThreatMetrics();
      setMetrics(response.data);
      setMeta(response.meta);

      // Append new time series data point for real-time chart
      const now = new Date();
      const timeStr = now.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });

      // Calculate incremental requests and drops
      const currentReqs = Math.floor(20 + Math.random() * 30);
      const highAlerts = response.data.recent_alerts.filter((a) => a.severity === 'HIGH');
      const blockedSample = highAlerts.length > 0 ? Math.floor(Math.random() * 8) + 1 : Math.floor(Math.random() * 2);
      const anomalyIndex = parseFloat(
        (0.12 + (blockedSample > 3 ? 0.65 : Math.random() * 0.2)).toFixed(2)
      );

      setTrafficHistory((prev) => {
        const updated = [
          ...prev,
          {
            time: timeStr,
            requests: currentReqs,
            blocked: blockedSample,
            anomalyScore: anomalyIndex,
          },
        ];
        // Keep sliding window of latest 15 points
        return updated.length > 15 ? updated.slice(updated.length - 15) : updated;
      });
    } catch (err) {
      console.error('Polling error in threat defender dashboard:', err);
    } finally {
      isPollingRef.current = false;
      if (isManual) setLoading(false);
    }
  }, []);

  // 2-second real-time polling effect
  useEffect(() => {
    // Initial fetch on mount
    pollData();

    // 1500ms polling interval
    const interval = setInterval(() => {
      pollData();
    }, 1500);

    return () => clearInterval(interval);
  }, [pollData]);

  // Handler for manual refresh
  const handleRefresh = useCallback(() => {
    pollData(true);
  }, [pollData]);

  // Handler for unblocking an IP from the dashboard
  const handleUnblockIp = useCallback(async (ipToUnblock: string) => {
    setMetrics((prev) => ({
      ...prev,
      blocked_ips_count: Math.max(0, prev.blocked_ips_count - 1),
      blocked_ips_list: prev.blocked_ips_list.filter((ip) => ip !== ipToUnblock),
    }));
    await unblockIpOnBackend(ipToUnblock);
  }, []);

  // Handler for changing API sampling rate
  const handleSamplingRateChange = useCallback(async (newRate: number) => {
    setSamplingRate(newRate);
    setMetrics((prev) => ({
      ...prev,
      sampling_rate: newRate,
      sampling_rate_pct: Math.round(newRate * 100),
      compute_saved_pct: Math.round((1.0 - newRate) * 100),
    }));
    await updateSamplingConfig(newRate);
  }, []);

  // Handler for triggering an immediate attack simulation spike
  const handleTriggerSimulatedAttack = useCallback(async () => {
    // Trigger real attacks against live backend if available
    // triggerLiveAttackApi('sqli');

    const randomIp = `185.220.${Math.floor(Math.random() * 200) + 10}.${Math.floor(Math.random() * 250) + 1}`;
    const spikeAlert: ThreatAlert = {
      id: `ALT-SIM-${Date.now().toString().slice(-4)}`,
      timestamp: new Date().toISOString(),
      severity: 'HIGH',
      message: `CRITICAL ATTACK SPIKE: Multi-threaded credential stuffing & SQLi detected from simulated botnet node ${randomIp}`,
    };

    setMetrics((prev) => ({
      ...prev,
      total_requests: prev.total_requests + 320,
      blocked_ips_count: prev.blocked_ips_count + 1,
      blocked_ips_list: [randomIp, ...prev.blocked_ips_list],
      recent_alerts: [spikeAlert, ...prev.recent_alerts.slice(0, 19)],
    }));

    // Inject spike to chart immediately
    const timeStr = new Date().toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });

    setTrafficHistory((prev) => [
      ...prev.slice(-14),
      {
        time: timeStr,
        requests: 180,
        blocked: 42,
        anomalyScore: 0.98,
      },
    ]);
  }, []);

  return (
    <div className="flex flex-col lg:flex-row h-screen overflow-hidden bg-[#080b11]">
      {/* Left Panel: Attacker Console (40%) */}
      <div className="lg:w-[40%] h-1/2 lg:h-full p-4 lg:p-6 border-b lg:border-b-0 lg:border-r border-white/[0.06] overflow-y-auto">
        <AttackerConsole />
      </div>

      {/* Right Panel: Defender CISO Dashboard (60%) */}
      <div className="lg:w-[60%] h-1/2 lg:h-full overflow-y-auto">
        <Dashboard
          metrics={metrics}
          meta={meta}
          trafficHistory={trafficHistory}
          loading={loading}
          samplingRate={samplingRate}
          onRefresh={handleRefresh}
          onUnblockIp={handleUnblockIp}
          onSamplingRateChange={handleSamplingRateChange}
          onTriggerSimulatedAttack={handleTriggerSimulatedAttack}
        />
      </div>
    </div>
  );
}
