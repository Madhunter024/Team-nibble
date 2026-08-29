"use client";

import React, { useState } from 'react';
import { AreaChart } from '@tremor/react';
import { Activity } from 'lucide-react';
import { TrafficDataPoint } from '../lib/mockData';

interface TrafficChartProps {
  data: TrafficDataPoint[];
}

export const TrafficChart: React.FC<TrafficChartProps> = ({ data = [] }) => {
  const [selectedView, setSelectedView] = useState<'all' | 'requests' | 'blocked'>('all');

  const getCategories = () => {
    switch (selectedView) {
      case 'requests':
        return ['requests'];
      case 'blocked':
        return ['blocked'];
      case 'all':
      default:
        return ['requests', 'blocked'];
    }
  };

  const getColors = () => {
    switch (selectedView) {
      case 'requests':
        return ['cyan'];
      case 'blocked':
        return ['rose'];
      case 'all':
      default:
        return ['cyan', 'rose'];
    }
  };

  const latestPoint = data.length > 0 ? data[data.length - 1] : { requests: 0, blocked: 0 };

  return (
    <div className="glass-panel p-6 shadow-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
        <div>
          <div className="flex items-center gap-2.5">
            <h3 className="text-base font-semibold text-slate-100 tracking-tight">
              Traffic Overview
            </h3>
            <span className="flex items-center gap-1.5 px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-medium tracking-wide rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              LIVE
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time request activity
          </p>
        </div>

        {/* Stream Filter & Current Velocity */}
        <div className="flex items-center gap-3">
          <div className="flex items-center bg-slate-950/60 p-0.5 rounded-lg border border-white/[0.06] text-xs">
            <button
              onClick={() => setSelectedView('all')}
              className={`px-3 py-1 rounded-md transition-colors text-xs font-medium ${
                selectedView === 'all'
                  ? 'bg-slate-800/90 text-slate-100 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setSelectedView('requests')}
              className={`px-3 py-1 rounded-md transition-colors text-xs font-medium ${
                selectedView === 'requests'
                  ? 'bg-slate-800/90 text-cyan-300 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Requests
            </button>
            <button
              onClick={() => setSelectedView('blocked')}
              className={`px-3 py-1 rounded-md transition-colors text-xs font-medium ${
                selectedView === 'blocked'
                  ? 'bg-slate-800/90 text-rose-300 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Blocked
            </button>
          </div>

          <div className="hidden sm:flex items-center gap-2 pl-3 border-l border-white/[0.06] text-xs font-mono text-slate-300">
            <span className="text-slate-400">Current:</span>
            <span className="text-cyan-400 font-semibold">{latestPoint.requests} req/s</span>
          </div>
        </div>
      </div>

      {/* Area Chart */}
      <div className="h-60 mt-4 w-full">
        <AreaChart
          className="h-60"
          data={data}
          index="time"
          categories={getCategories()}
          colors={getColors()}
          valueFormatter={(val: number) => `${val.toLocaleString()} req`}
          yAxisWidth={68}
          showGridLines={true}
          curveType="monotone"
          showLegend={false}
          showAnimation={false}
        />
      </div>

      {/* Legend */}
      <div className="mt-3 pt-3 border-t border-white/[0.04] flex flex-wrap items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
            <span className="text-[11px]">Ingress volume</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-rose-500"></span>
            <span className="text-[11px]">Blocked sources</span>
          </div>
        </div>
        <div className="text-[11px] text-slate-500 font-mono">
          2s refresh window
        </div>
      </div>
    </div>
  );
};
