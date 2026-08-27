import { useEffect, useState } from 'react';
import { Navbar } from '../components/Navbar';
import { fetchAnomalies, runAnomalyDetection } from '../services/risk_intelligence';
import type { Anomaly } from '../types/risk_intelligence';

export const AnomaliesPage = () => {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [serviceFilter, setServiceFilter] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAnomalies = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAnomalies(serviceFilter || undefined);
      setAnomalies(data);
    } catch (err) {
      setError('Failed to load detected anomalies.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadAnomalies();
  }, [serviceFilter]);

  const handleRunDetection = async () => {
    setLoading(true);
    setError(null);
    try {
      await runAnomalyDetection(serviceFilter || undefined);
      await loadAnomalies();
    } catch (err) {
      setError('Anomaly detection execution failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell min-h-screen bg-[#E8DCC8] text-[#3B3025] font-sans">
      <Navbar />

      <main className="mx-auto max-w-7xl px-6 py-10 space-y-8">
        <header className="rounded-3xl border border-slate-800 bg-slate-900/70 p-8 shadow-2xl backdrop-blur-md">
          <p className="mb-2 text-xs font-bold uppercase tracking-[0.25em] text-cyan-400">
            STACKSENSE
          </p>
          <h1 className="text-3xl font-bold sm:text-4xl">Production Anomaly Detection</h1>
          <p className="mt-3 max-w-3xl text-base text-slate-300">
            Detect unusual production behavior (error rate spikes, critical event frequency, service anomalies) by aggregating application logs into 5-minute time windows using Isolation Forest algorithms.
          </p>
        </header>

        {/* Action Controls */}
        <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <input
              type="text"
              placeholder="Filter by service name..."
              value={serviceFilter}
              onChange={(e) => setServiceFilter(e.target.value)}
              className="w-72 rounded-2xl border border-slate-700 bg-slate-950 px-4 py-2.5 text-sm text-slate-100 focus:border-cyan-500 focus:outline-none"
            />

            <button
              onClick={handleRunDetection}
              disabled={loading}
              className="rounded-2xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 px-6 py-2.5 text-sm font-semibold text-slate-950 transition-all shadow-lg shadow-cyan-500/20"
            >
              {loading ? 'Detecting Anomalies…' : 'Run Anomaly Detection'}
            </button>
          </div>
          {error && <p className="text-sm font-medium text-red-400">{error}</p>}
        </section>

        {/* Anomalies List Grid */}
        <section className="space-y-4">
          <h3 className="text-xl font-semibold text-slate-100">Detected Events & Anomalies</h3>

          {anomalies.length === 0 ? (
            <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-8 text-center text-slate-400">
              No anomalies detected yet. Click "Run Anomaly Detection" to analyze application event streams.
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {anomalies.map((anom) => (
                <div
                  key={anom.id}
                  className={`rounded-3xl border p-6 shadow-xl transition-all ${
                    anom.is_anomaly
                      ? 'border-red-500/40 bg-gradient-to-br from-red-950/30 to-slate-900'
                      : 'border-slate-800 bg-slate-900/70'
                  }`}
                >
                  <div className="flex items-center justify-between border-b border-slate-800/80 pb-4 mb-4">
                    <div>
                      <span className="font-mono text-xs text-slate-400 uppercase tracking-wider">Service</span>
                      <h4 className="text-lg font-bold text-slate-100">{anom.service_name}</h4>
                    </div>
                    {anom.is_anomaly ? (
                      <span className="rounded-full bg-red-500/20 px-3 py-1 text-xs font-bold text-red-400 border border-red-500/40 animate-pulse">
                        ANOMALY DETECTED
                      </span>
                    ) : (
                      <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400 border border-emerald-500/30">
                        NORMAL
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-xs font-mono">
                    <div>
                      <p className="text-slate-500">Anomaly Score</p>
                      <p className="text-base font-bold text-amber-400">{anom.anomaly_score}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Error Rate</p>
                      <p className="text-base font-bold text-red-400">
                        {(anom.metrics_snapshot.error_rate * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-500">Total Events</p>
                      <p className="text-slate-200">{anom.metrics_snapshot.total_events}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Error / Critical</p>
                      <p className="text-slate-200">
                        {anom.metrics_snapshot.error_count} / {anom.metrics_snapshot.critical_count}
                      </p>
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-800/60 text-xs text-slate-400">
                    Window: {new Date(anom.window_start).toLocaleTimeString()} –{' '}
                    {new Date(anom.window_end).toLocaleTimeString()} ({anom.detection_method})
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
};
