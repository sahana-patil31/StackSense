import { useEffect, useState } from 'react';
import { Navbar } from '../components/Navbar';
import { analyzeDeploymentRisk, fetchRiskAnalyses } from '../services/risk_intelligence';
import { fetchDeployments } from '../services/ingestion';
import type { DeploymentRiskAnalysis } from '../types/risk_intelligence';
import type { Deployment } from '../types/ingestion';

const RISK_BADGES: Record<string, string> = {
  LOW: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  MEDIUM: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  HIGH: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
  CRITICAL: 'bg-red-500/10 text-red-400 border-red-500/30 animate-pulse',
};

export const RiskDashboardPage = () => {
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [selectedDepId, setSelectedDepId] = useState<string>('');
  const [currentAnalysis, setCurrentAnalysis] = useState<DeploymentRiskAnalysis | null>(null);
  const [historicalAnalyses, setHistoricalAnalyses] = useState<DeploymentRiskAnalysis[]>([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [deps, history] = await Promise.all([fetchDeployments(), fetchRiskAnalyses()]);
        setDeployments(deps);
        setHistoricalAnalyses(history);
        if (deps.length > 0) {
          setSelectedDepId(deps[0].id);
        }
      } catch (err) {
        setError('Failed to fetch deployment risk data.');
      }
    };
    void loadData();
  }, []);

  const handleAnalyzeRisk = async () => {
    if (!selectedDepId) return;
    setLoading(true);
    setError(null);
    try {
      const analysis = await analyzeDeploymentRisk(selectedDepId);
      setCurrentAnalysis(analysis);
      const updatedHistory = await fetchRiskAnalyses();
      setHistoricalAnalyses(updatedHistory);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Deployment risk analysis failed.');
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
          <h1 className="text-3xl font-bold sm:text-4xl">Deployment Risk Prediction</h1>
          <p className="mt-3 max-w-3xl text-base text-slate-300">
            Calculate deployment risk scores (0–100) using Random Forest ML models trained on commit blast radius, code entity changes, dependency graph density, and historical deployment failures.
          </p>
        </header>

        {/* Action Controls */}
        <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl space-y-4">
          <h2 className="text-xl font-semibold text-slate-100">Analyze Deployment Risk</h2>
          <div className="flex flex-wrap items-center gap-4">
            <select
              value={selectedDepId}
              onChange={(e) => setSelectedDepId(e.target.value)}
              className="min-w-[300px] rounded-2xl border border-slate-700 bg-slate-950 px-4 py-2.5 text-sm text-slate-100 focus:border-cyan-500 focus:outline-none"
            >
              {deployments.length === 0 ? (
                <option value="">No deployments available</option>
              ) : (
                deployments.map((d) => (
                  <option key={d.id} value={d.id}>
                    Deployment #{d.id.substring(0, 8)} ({d.environment} - {d.service_name || 'default'})
                  </option>
                ))
              )}
            </select>

            <button
              onClick={handleAnalyzeRisk}
              disabled={loading || !selectedDepId}
              className="rounded-2xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 px-6 py-2.5 text-sm font-semibold text-slate-950 transition-all shadow-lg shadow-cyan-500/20"
            >
              {loading ? 'Calculating Risk…' : 'Analyze Deployment'}
            </button>
          </div>
          {error && <p className="text-sm font-medium text-red-400">{error}</p>}
        </section>

        {/* Current Risk Analysis Result */}
        {currentAnalysis && (
          <section className="rounded-3xl border border-slate-800 bg-slate-900/80 p-8 shadow-2xl space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-6">
              <div>
                <p className="text-xs uppercase tracking-wider text-slate-400">Deployment Risk Analysis</p>
                <h3 className="text-2xl font-bold text-slate-100">
                  Deployment #{currentAnalysis.deployment_id.substring(0, 8)}
                </h3>
              </div>
              <span
                className={`rounded-full border px-4 py-1.5 text-sm font-bold uppercase tracking-wider ${
                  RISK_BADGES[currentAnalysis.risk_level] || RISK_BADGES.LOW
                }`}
              >
                {currentAnalysis.risk_level} RISK
              </span>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
              <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-6">
                <p className="text-xs uppercase tracking-wider text-slate-400">Risk Score</p>
                <div className="mt-3 flex items-baseline gap-2">
                  <span className="text-5xl font-black text-cyan-400">{currentAnalysis.risk_score}</span>
                  <span className="text-lg text-slate-400">/ 100</span>
                </div>
              </div>

              <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-6">
                <p className="text-xs uppercase tracking-wider text-slate-400">Failure Probability</p>
                <div className="mt-3">
                  <span className="text-4xl font-extrabold text-purple-400">
                    {(currentAnalysis.failure_probability * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-6">
                <p className="text-xs uppercase tracking-wider text-slate-400">Model Version</p>
                <div className="mt-3 font-mono text-lg text-slate-200">{currentAnalysis.model_version}</div>
              </div>
            </div>

            {/* Factor Explanation */}
            <div className="space-y-4">
              <h4 className="text-lg font-semibold text-slate-200">Contributing Risk Factors</h4>
              <div className="grid gap-3 sm:grid-cols-2">
                {currentAnalysis.contributing_factors.map((factor, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-3 rounded-2xl border border-slate-800 bg-slate-950/60 p-4"
                  >
                    <span
                      className={`mt-0.5 rounded px-2 py-0.5 text-[10px] font-bold uppercase ${
                        factor.impact === 'HIGH'
                          ? 'bg-red-500/10 text-red-400 border border-red-500/30'
                          : factor.impact === 'MEDIUM'
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                          : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                      }`}
                    >
                      {factor.impact}
                    </span>
                    <div>
                      <p className="text-sm font-semibold text-slate-200">{factor.description}</p>
                      <p className="font-mono text-xs text-slate-400">Value: {String(factor.feature_value)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* Historical Analyses Table */}
        <section className="overflow-x-auto rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl">
          <h3 className="mb-4 text-xl font-semibold text-slate-100">Historical Deployment Risk Assessments</h3>
          {historicalAnalyses.length === 0 ? (
            <p className="text-sm text-slate-400">No risk assessments recorded yet.</p>
          ) : (
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="border-b border-slate-800 text-xs uppercase tracking-wider text-slate-400">
                <tr>
                  <th className="pb-3 font-semibold">Deployment</th>
                  <th className="pb-3 font-semibold">Risk Score</th>
                  <th className="pb-3 font-semibold">Risk Level</th>
                  <th className="pb-3 font-semibold">Failure Prob</th>
                  <th className="pb-3 font-semibold">Model Version</th>
                  <th className="pb-3 font-semibold">Assessed At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                {historicalAnalyses.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/40">
                    <td className="py-3 font-semibold text-slate-200">#{item.deployment_id.substring(0, 8)}</td>
                    <td className="py-3 font-bold text-cyan-400">{item.risk_score} / 100</td>
                    <td className="py-3">
                      <span
                        className={`inline-block rounded-full border px-2.5 py-0.5 text-[11px] font-semibold uppercase ${
                          RISK_BADGES[item.risk_level] || RISK_BADGES.LOW
                        }`}
                      >
                        {item.risk_level}
                      </span>
                    </td>
                    <td className="py-3 text-purple-400">{(item.failure_probability * 100).toFixed(1)}%</td>
                    <td className="py-3 text-slate-400">{item.model_version}</td>
                    <td className="py-3 text-slate-400">{new Date(item.created_at).toLocaleString()}</td>
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
