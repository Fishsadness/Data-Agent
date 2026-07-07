import { useState, useEffect } from 'react';
import { AlertTriangle, TrendingUp, Activity, BarChart3 } from 'lucide-react';
import { healthCheck } from '../../api';

interface DashboardPanelProps {
  activePanel: string;
}

export function DashboardPanel({ activePanel }: DashboardPanelProps) {
  const [alerts, setAlerts] = useState<Array<{rule: string; severity: string; value: number; threshold: number}>>([]);
  const [trend, setTrend] = useState<{trend?: string; change_pct?: number; data?: Array<{day: string; count: number}>}>({});
  const [health, setHealth] = useState<Record<string, string>>({});

  useEffect(() => {
    if (activePanel !== 'dashboard') return;

    // Fetch dashboard data
    healthCheck().then(setHealth).catch(console.error);

    fetch('/api/alert/check')
      .then(r => r.json())
      .then(d => setAlerts(d.alerts || []))
      .catch(console.error);

    fetch('/api/alert/trend?metric=orders&days=7')
      .then(r => r.json())
      .then(d => setTrend(d))
      .catch(console.error);
  }, [activePanel]);

  if (activePanel !== 'dashboard') return null;

  return (
    <div className="flex-1 overflow-y-auto p-6 paper-texture dark:paper-texture-dark">
      <div className="max-w-4xl mx-auto space-y-6">
        <h3 className="font-serif uppercase tracking-[0.3em] text-xs text-vintage-brown/60 dark:text-vintage-amber/60">
          System Dashboard
        </h3>

        {/* Status Cards */}
        <div className="grid grid-cols-3 gap-4">
          <div className="border-2 border-vintage-brown dark:border-vintage-amber p-4 shadow-vintage-sm">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-4 h-4 text-vintage-forest" />
              <span className="text-[10px] uppercase tracking-[0.15em] font-serif text-vintage-brown/60 dark:text-vintage-amber/60">
                System
              </span>
            </div>
            <span className="font-serif text-lg text-vintage-ink dark:text-vintage-cream">
              {health.status === 'ok' ? 'Operational' : 'Degraded'}
            </span>
          </div>

          <div className="border-2 border-vintage-brown dark:border-vintage-amber p-4 shadow-vintage-sm">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-4 h-4 text-vintage-accent" />
              <span className="text-[10px] uppercase tracking-[0.15em] font-serif text-vintage-brown/60 dark:text-vintage-amber/60">
                Alerts
              </span>
            </div>
            <span className="font-serif text-lg text-vintage-ink dark:text-vintage-cream">
              {alerts.length} Active
            </span>
          </div>

          <div className="border-2 border-vintage-brown dark:border-vintage-amber p-4 shadow-vintage-sm">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-4 h-4 text-vintage-brown" />
              <span className="text-[10px] uppercase tracking-[0.15em] font-serif text-vintage-brown/60 dark:text-vintage-amber/60">
                Trend
              </span>
            </div>
            <span className="font-serif text-lg text-vintage-ink dark:text-vintage-cream">
              {trend.trend || '--'}
            </span>
          </div>
        </div>

        {/* Alerts */}
        {alerts.length > 0 && (
          <div className="border-2 border-vintage-brown dark:border-vintage-amber shadow-vintage-sm overflow-hidden">
            <div className="px-4 py-2.5 border-b-2 border-vintage-brown/30 dark:border-vintage-amber/30">
              <span className="text-[10px] uppercase tracking-[0.2em] font-serif text-vintage-brown dark:text-vintage-amber">
                Active Alerts
              </span>
            </div>
            <div className="divide-y divide-vintage-brown/10 dark:divide-vintage-amber/10">
              {alerts.map((a, i) => (
                <div
                  key={i}
                  className="flex items-center gap-3 px-4 py-3 hover:bg-vintage-wheat/30 dark:hover:bg-vintage-ink/20 transition-colors duration-700"
                >
                  <span className={`w-2 h-2 border ${
                    a.severity === 'critical' ? 'bg-vintage-accent border-vintage-accent' : 'bg-vintage-amber border-vintage-amber'
                  }`} />
                  <span className="flex-1 font-serif text-sm text-vintage-ink dark:text-vintage-cream">
                    {a.rule}
                  </span>
                  <span className="text-[10px] uppercase tracking-[0.15em] font-serif text-vintage-brown/50 dark:text-vintage-amber/50">
                    {a.value} / {a.threshold}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Trend Data */}
        {trend.data && (
          <div className="border-2 border-vintage-brown dark:border-vintage-amber shadow-vintage-sm overflow-hidden">
            <div className="px-4 py-2.5 border-b-2 border-vintage-brown/30 dark:border-vintage-amber/30">
              <span className="text-[10px] uppercase tracking-[0.2em] font-serif text-vintage-brown dark:text-vintage-amber">
                7-Day Trend
              </span>
            </div>
            <div className="p-4 overflow-x-auto">
              <table className="w-full text-sm font-serif">
                <thead>
                  <tr className="border-b border-vintage-brown/20 dark:border-vintage-amber/20">
                    <th className="text-left py-2 text-[10px] uppercase tracking-[0.15em] text-vintage-brown/60 dark:text-vintage-amber/60">Day</th>
                    <th className="text-right py-2 text-[10px] uppercase tracking-[0.15em] text-vintage-brown/60 dark:text-vintage-amber/60">Count</th>
                  </tr>
                </thead>
                <tbody>
                  {(trend.data || []).map((d, i) => (
                    <tr key={i} className="border-b border-vintage-brown/10 dark:border-vintage-amber/10">
                      <td className="py-2 text-vintage-ink dark:text-vintage-cream">{d.day}</td>
                      <td className="text-right py-2 text-vintage-ink dark:text-vintage-cream">{d.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}