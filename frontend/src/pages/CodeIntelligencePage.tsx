import { useEffect, useState } from 'react';
import { Navbar } from '../components/Navbar';
import { DependencyGraph } from '../components/code_analysis/DependencyGraph';
import {
  fetchCodeEntities,
  fetchRepositoryGraph,
  triggerRepositoryAnalysis,
} from '../services/code_analysis';
import { fetchRepositories } from '../services/ingestion';
import type { CodeEntity, GraphData } from '../types/code_analysis';
import type { Repository } from '../types/ingestion';

export const CodeIntelligencePage = () => {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [selectedRepoId, setSelectedRepoId] = useState<string>('');
  const [customPath, setCustomPath] = useState<string>('');

  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [entities, setEntities] = useState<CodeEntity[]>([]);
  const [activeTab, setActiveTab] = useState<'graph' | 'entities' | 'history'>('graph');

  const [analyzing, setAnalyzing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Load repositories on mount
  useEffect(() => {
    const loadRepos = async () => {
      try {
        const repos = await fetchRepositories();
        setRepositories(repos);
        if (repos.length > 0) {
          setSelectedRepoId(repos[0].id);
        }
      } catch (err) {
        setError('Failed to fetch repositories. Please ensure backend is running.');
      }
    };
    void loadRepos();
  }, []);

  // Fetch analysis data when selected repository changes
  useEffect(() => {
    if (!selectedRepoId) return;

    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [graph, ents] = await Promise.all([
          fetchRepositoryGraph(selectedRepoId),
          fetchCodeEntities(selectedRepoId),
        ]);
        setGraphData(graph);
        setEntities(ents);
      } catch (err) {
        setError('Unable to load code analysis data for selected repository.');
      } finally {
        setLoading(false);
      }
    };

    void loadData();
  }, [selectedRepoId]);

  const handleRunAnalysis = async () => {
    if (!selectedRepoId) return;
    setAnalyzing(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const run = await triggerRepositoryAnalysis(selectedRepoId, customPath || undefined);
      setSuccessMessage(
        `Analysis completed successfully! Analyzed ${run.files_analyzed} files, found ${run.entities_found} entities and ${run.relationships_found} relationships.`
      );
      // Refresh graph and entity data
      const [graph, ents] = await Promise.all([
        fetchRepositoryGraph(selectedRepoId),
        fetchCodeEntities(selectedRepoId),
      ]);
      setGraphData(graph);
      setEntities(ents);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Code analysis failed. Check repository directory path.');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="app-shell min-h-screen bg-[#E8DCC8] text-[#3B3025] font-sans">
      <Navbar />

      <main className="mx-auto max-w-7xl px-6 py-10 space-y-8">
        {/* Header Section */}
        <header className="rounded-3xl border border-slate-800 bg-slate-900/70 p-8 shadow-2xl backdrop-blur-md">
          <p className="mb-2 text-xs font-bold uppercase tracking-[0.25em] text-cyan-400">
            STACKSENSE
          </p>
          <h1 className="text-3xl font-bold sm:text-4xl">Code Intelligence & Structural Analysis</h1>
          <p className="mt-3 max-w-3xl text-base text-slate-300">
            Parse real source code repositories with Tree-sitter, extract Python, JavaScript, and TypeScript structural code entities, resolve module imports and function calls, and explore interactive dependency graphs.
          </p>
        </header>

        {/* Repository Selector & Analysis Controls */}
        <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl space-y-4">
          <h2 className="text-xl font-semibold text-slate-100">Select Repository to Analyze</h2>

          <div className="flex flex-wrap items-center gap-4">
            <select
              value={selectedRepoId}
              onChange={(e) => setSelectedRepoId(e.target.value)}
              className="min-w-[240px] rounded-2xl border border-slate-700 bg-slate-950 px-4 py-2.5 text-sm text-slate-100 focus:border-cyan-500 focus:outline-none"
            >
              {repositories.length === 0 ? (
                <option value="">No repositories available</option>
              ) : (
                repositories.map((repo) => (
                  <option key={repo.id} value={repo.id}>
                    {repo.name} ({repo.provider})
                  </option>
                ))
              )}
            </select>

            <input
              type="text"
              placeholder="Local directory path (optional, defaults to project root)..."
              value={customPath}
              onChange={(e) => setCustomPath(e.target.value)}
              className="flex-1 min-w-[300px] rounded-2xl border border-slate-700 bg-slate-950 px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:border-cyan-500 focus:outline-none font-mono text-xs"
            />

            <button
              onClick={handleRunAnalysis}
              disabled={analyzing || !selectedRepoId}
              className="rounded-2xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 px-6 py-2.5 text-sm font-semibold text-slate-950 transition-all shadow-lg shadow-cyan-500/20"
            >
              {analyzing ? 'Analyzing Repository…' : 'Run Code Analysis'}
            </button>
          </div>

          {error && <p className="text-sm font-medium text-red-400">{error}</p>}
          {successMessage && <p className="text-sm font-medium text-emerald-400">{successMessage}</p>}
        </section>

        {/* Metrics Overview Cards */}
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm">
            <p className="text-xs uppercase tracking-wider text-slate-400">Total Graph Nodes</p>
            <p className="mt-2 text-3xl font-bold text-cyan-400">{graphData.nodes.length}</p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm">
            <p className="text-xs uppercase tracking-wider text-slate-400">Total Relationships</p>
            <p className="mt-2 text-3xl font-bold text-purple-400">{graphData.edges.length}</p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm">
            <p className="text-xs uppercase tracking-wider text-slate-400">Code Entities</p>
            <p className="mt-2 text-3xl font-bold text-emerald-400">{entities.length}</p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm">
            <p className="text-xs uppercase tracking-wider text-slate-400">Resolved Imports/Calls</p>
            <p className="mt-2 text-3xl font-bold text-amber-400">
              {graphData.edges.filter((e) => e.resolved).length}
            </p>
          </div>
        </section>

        {/* Tab Navigation */}
        <section className="space-y-6">
          <div className="flex border-b border-slate-800 text-sm font-medium">
            <button
              onClick={() => setActiveTab('graph')}
              className={`pb-3 px-6 border-b-2 transition-colors ${
                activeTab === 'graph'
                  ? 'border-cyan-400 text-cyan-400 font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Dependency Graph
            </button>

            <button
              onClick={() => setActiveTab('entities')}
              className={`pb-3 px-6 border-b-2 transition-colors ${
                activeTab === 'entities'
                  ? 'border-cyan-400 text-cyan-400 font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Extracted Entities ({entities.length})
            </button>
          </div>

          {/* Tab 1: Dependency Graph */}
          {activeTab === 'graph' && (
            loading ? (
              <div className="flex h-64 items-center justify-center text-slate-400">
                Loading repository graph data…
              </div>
            ) : (
              <DependencyGraph data={graphData} />
            )
          )}

          {/* Tab 2: Code Entities Table */}
          {activeTab === 'entities' && (
            <div className="overflow-x-auto rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl">
              <h3 className="mb-4 text-xl font-semibold text-slate-100">Extracted Code Entities</h3>
              {entities.length === 0 ? (
                <p className="text-sm text-slate-400">No entities extracted yet for this repository.</p>
              ) : (
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="border-b border-slate-800 text-xs uppercase tracking-wider text-slate-400">
                    <tr>
                      <th className="pb-3 font-semibold">Entity Name</th>
                      <th className="pb-3 font-semibold">Type</th>
                      <th className="pb-3 font-semibold">Lines</th>
                      <th className="pb-3 font-semibold">Qualified Identifier</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                    {entities.map((e) => (
                      <tr key={e.id} className="hover:bg-slate-800/40">
                        <td className="py-3 font-semibold text-slate-100">{e.name}</td>
                        <td className="py-3">
                          <span className="rounded bg-slate-800 px-2 py-0.5 font-bold text-cyan-400">
                            {e.entity_type}
                          </span>
                        </td>
                        <td className="py-3 text-slate-400">
                          {e.start_line} – {e.end_line}
                        </td>
                        <td className="py-3 text-slate-400">{e.qualified_name || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </section>
      </main>
    </div>
  );
};
