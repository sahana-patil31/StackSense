import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { fetchOverview, fetchSystemHealth } from '../services/api';
import type { Overview, SystemHealth } from '../types/overview';

const DashboardPage = () => {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadDashboard = async () => {
      const [overviewResult, healthResult] = await Promise.allSettled([fetchOverview(), fetchSystemHealth()]);
      if (overviewResult.status === 'fulfilled') setOverview(overviewResult.value);
      else setError('Unable to load engineering overview data.');
      if (healthResult.status === 'fulfilled') setSystemHealth(healthResult.value);
      else setError((current) => current || 'Unable to load system health.');
      setLoading(false);
    };

    void loadDashboard();
  }, []);

  const metrics: Array<[string, number]> = [
    ['Repositories', overview?.repositories ?? 0],
    ['Active incidents', overview?.active_incidents ?? 0],
    ['High-risk deployments', overview?.high_risk_deployments ?? 0],
    ['Anomalies', overview?.anomalies ?? 0],
  ];

  return (
    <div className="dashboard-theme min-h-screen bg-[#E8DCC8] text-[#3B3025] font-sans">
      <Navbar />

      <main className="mx-auto flex max-w-6xl flex-col gap-8 px-6 py-12">
        <header className="rounded-3xl border border-[#C5AD8A] bg-[#F5EFE6] p-8 shadow-2xl shadow-[#8E7658]/20">
          <p className="mb-3 text-sm uppercase tracking-[0.3em] text-[#3B3025]">STACKSENSE</p>
          <h1 className="text-4xl font-semibold sm:text-5xl">AI-Powered Engineering Intelligence</h1>
          <p className="mt-4 max-w-3xl text-lg text-[#6B5B4A]">
            STACKSENSE helps engineering teams understand code, deployments, dependencies, and production incidents with a calm and reliable foundation.
          </p>
        </header>

        <section className="rounded-3xl border border-[#C5AD8A] bg-[#F5EFE6] p-8 shadow-xl shadow-[#8E7658]/15">
          <div className="flex flex-wrap items-center justify-between gap-6">
            <div className="space-y-2 max-w-2xl">
              <h2 className="text-2xl font-bold">Code Intelligence & AST Parsing</h2>
              <p className="text-sm text-[#6B5B4A]">
                Parse Python, JavaScript, and TypeScript repositories using Tree-sitter. Extract files, classes, functions, methods, imports, and calls into an interactive dependency graph.
              </p>
            </div>
            <Link
              to="/code-intelligence"
              className="rounded-2xl bg-[#5B4636] px-6 py-3 text-sm font-semibold text-white transition-all shadow-lg shadow-[#8E7658]/25 hover:bg-[#463528]"
            >
              Explore Code Intelligence →
            </Link>
          </div>
        </section>

        {error && <p className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">{error}</p>}
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {metrics.map(([label, value]) => <div key={String(label)} className="rounded-2xl border border-[#C5AD8A] bg-[#F5EFE6] p-5"><p className="text-xs uppercase tracking-wider text-[#6B5B4A]">{label}</p><p className="mt-3 text-3xl font-bold text-[#3B3025]">{loading ? '...' : value}</p></div>)}
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
          <div className="rounded-3xl border border-[#C5AD8A] bg-[#F5EFE6] p-6"><div className="flex items-center justify-between"><h2 className="text-xl font-semibold text-[#3B3025]">Recent activity</h2><Link to="/risk" className="text-sm text-[#6B5B4A] hover:text-[#8B6F47]">Risk analysis</Link></div><div className="mt-5 divide-y divide-[#C5AD8A]/60">{overview?.recent_deployments.length ? overview.recent_deployments.map((item) => <div key={item.id} className="flex items-center justify-between py-3 text-sm"><span className="text-[#6B5B4A]">Deployment <span className="font-mono text-[#6B5B4A]">#{item.id.slice(0, 8)}</span> {item.service_name || 'service'}</span><span className="rounded-full border border-[#C5AD8A] px-2 py-1 text-xs uppercase text-[#6B5B4A]">{item.status}</span></div>) : <p className="py-6 text-sm text-[#6B5B4A]">No recent deployments recorded.</p>}</div></div>
          <div className="rounded-3xl border border-[#C5AD8A] bg-[#F5EFE6] p-6"><h2 className="text-xl font-semibold text-[#3B3025]">System health</h2><div className="mt-5 space-y-3 text-sm">{systemHealth ? Object.entries({ API: systemHealth.api, Database: systemHealth.database, 'Vector search': systemHealth.vector_search, 'Risk model': systemHealth.risk_model, Embeddings: systemHealth.embedding_provider, LLM: systemHealth.llm }).map(([label, value]) => <div key={label} className="flex items-center justify-between border-b border-[#C5AD8A]/60 pb-3"><span className="text-[#6B5B4A]">{label}</span><span className="text-[#3B3025]">{value}</span></div>) : <p className="text-[#6B5B4A]">Checking dependencies...</p>}</div></div>
        </section>
      </main>
    </div>
  );
};

export default DashboardPage;
