import { useEffect, useState } from 'react';
import { Navbar } from '../components/Navbar';
import { analyzeRootCause, fetchAnomalies, fetchIncidents } from '../services/risk_intelligence';
import type { Anomaly, Incident, RootCauseAnalysis } from '../types/risk_intelligence';

const SEVERITY_BADGES: Record<string, string> = {
  low: 'bg-slate-500/10 text-slate-400 border-slate-500/30',
  medium: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  high: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
  critical: 'bg-red-500/10 text-red-400 border-red-500/30 animate-pulse',
};

export const IncidentsPage = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [selectedAnomalyId, setSelectedAnomalyId] = useState<string>('');
  const [rootCauseResults, setRootCauseResults] = useState<RootCauseAnalysis[]>([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [incList, anomList] = await Promise.all([
          fetchIncidents(),
          fetchAnomalies(undefined, true), // fetch true anomalies
        ]);
        setIncidents(incList);
        setAnomalies(anomList);
        if (anomList.length > 0) {
          setSelectedAnomalyId(anomList[0].id);
        }
      } catch (err: any) {
        setError(
          err?.response?.status === 503
            ? 'Database unavailable. Start PostgreSQL to load incident data.'
            : 'Failed to load incident data.'
        );
      }
    };
    void loadData();
  }, []);

  const handleAnalyzeIncident = async () => {
    if (!selectedAnomalyId) return;
    setLoading(true);
    setError(null);
    try {
      const candidates = await analyzeRootCause(selectedAnomalyId);
      setRootCauseResults(candidates);
      const updatedIncidents = await fetchIncidents();
      setIncidents(updatedIncidents);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Incident root cause analysis failed.');
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
          <h1 className="text-3xl font-bold sm:text-4xl">Root-Cause Correlation & Incident Intelligence</h1>
          <p className="mt-3 max-w-3xl text-base text-slate-300">
            Correlate production anomalies with recent deployments, commit changes, and dependency graphs to establish evidence-based probable root causes without hallucination.
          </p>
        </header>

        {/* Action Controls */}
        <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl space-y-4">
          <h2 className="text-xl font-semibold text-slate-100">Analyze Anomaly for Root Cause</h2>
          <div className="flex flex-wrap items-center gap-4">
            <select
              value={selectedAnomalyId}
              onChange={(e) => setSelectedAnomalyId(e.target.value)}
              className="min-w-[320px] rounded-2xl border border-slate-700 bg-slate-950 px-4 py-2.5 text-sm text-slate-100 focus:border-cyan-500 focus:outline-none"
            >
              {anomalies.length === 0 ? (
                <option value="">No active anomalies available for analysis</option>
              ) : (
                anomalies.map((a) => (
                  <option key={a.id} value={a.id}>
                    Anomaly in {a.service_name} (Score: {a.anomaly_score})
                  </option>
                ))
              )}
            </select>

            <button
              onClick={handleAnalyzeIncident}
              disabled={loading || !selectedAnomalyId}
              className="rounded-2xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 px-6 py-2.5 text-sm font-semibold text-slate-950 transition-all shadow-lg shadow-cyan-500/20"
            >
              {loading ? 'Correlating Root Cause…' : 'Analyze Probable Cause'}
            </button>
          </div>
          {error && <p className="text-sm font-medium text-red-400">{error}</p>}
        </section>

        {/* Root Cause Candidate Evidence Breakdown */}
        {rootCauseResults.length > 0 && (
          <section className="rounded-3xl border border-purple-500/30 bg-slate-900/80 p-8 shadow-2xl space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-purple-400">Probable Root Cause Analysis</p>
                <h3 className="text-2xl font-bold text-slate-100">Ranked Candidate Causes</h3>
              </div>
            </div>

            <div className="space-y-4">
              {rootCauseResults.map((candidate, idx) => (
                <div
                  key={candidate.id || idx}
                  className="rounded-2xl border border-slate-800 bg-slate-950/70 p-6 space-y-4 shadow-lg"
                >
                  <div className="flex flex-wrap items-center justify-between gap-4">
                    <div>
                      <span className="rounded bg-slate-800 px-2 py-0.5 font-mono text-xs font-bold text-cyan-400 uppercase">
                        {candidate.candidate_type}
                      </span>
                      <p className="font-mono text-base font-bold text-slate-100 mt-1">
                        ID: #{candidate.candidate_id.substring(0, 12)}
                      </p>
                    </div>

                    <div className="text-right">
                      <p className="text-xs uppercase text-slate-400 font-medium">Confidence Score</p>
                      <p className="text-2xl font-extrabold text-purple-400">{candidate.confidence_score}%</p>
                    </div>
                  </div>

                  {/* Evidence List */}
                  <div className="space-y-2">
                    <p className="text-xs uppercase font-semibold text-slate-400 tracking-wider">Supporting Evidence</p>
                    <div className="grid gap-2 sm:grid-cols-2">
                      {candidate.evidence.map((ev, evIdx) => (
                        <div
                          key={evIdx}
                          className="rounded-xl border border-slate-800/80 bg-slate-900/60 p-3 text-xs space-y-1"
                        >
                          <div className="flex items-center justify-between font-semibold">
                            <span className="text-cyan-400 uppercase font-mono">{ev.evidence_type}</span>
                            <span className="text-slate-300">+{ev.score} pts</span>
                          </div>
                          <p className="text-slate-300 font-sans">{ev.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Incidents Table */}
        <section className="overflow-x-auto rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl">
          <h3 className="mb-4 text-xl font-semibold text-slate-100">Production Incidents</h3>
          {incidents.length === 0 ? (
            <p className="text-sm text-slate-400">No incidents recorded yet.</p>
          ) : (
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="border-b border-slate-800 text-xs uppercase tracking-wider text-slate-400">
                <tr>
                  <th className="pb-3 font-semibold">Incident Title</th>
                  <th className="pb-3 font-semibold">Severity</th>
                  <th className="pb-3 font-semibold">Status</th>
                  <th className="pb-3 font-semibold">Probable Cause</th>
                  <th className="pb-3 font-semibold">Confidence</th>
                  <th className="pb-3 font-semibold">Detected At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                {incidents.map((inc) => (
                  <tr key={inc.id} className="hover:bg-slate-800/40">
                    <td className="py-3 font-semibold text-slate-100">{inc.title}</td>
                    <td className="py-3">
                      <span
                        className={`inline-block rounded-full border px-2.5 py-0.5 text-[11px] font-semibold uppercase ${
                          SEVERITY_BADGES[inc.severity] || SEVERITY_BADGES.medium
                        }`}
                      >
                        {inc.severity}
                      </span>
                    </td>
                    <td className="py-3 text-slate-300 uppercase">{inc.status}</td>
                    <td className="py-3 text-cyan-400 font-sans max-w-xs truncate">{inc.probable_cause}</td>
                    <td className="py-3 text-purple-400 font-bold">{inc.confidence}%</td>
                    <td className="py-3 text-slate-400">{new Date(inc.detected_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </main>
    </div>
  );
};
