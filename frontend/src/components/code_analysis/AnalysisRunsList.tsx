import React from 'react';
import type { AnalysisRun } from '../../types/code_analysis';

interface AnalysisRunsListProps {
  runs: AnalysisRun[];
}

const STATUS_BADGES: Record<string, string> = {
  completed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  running: 'bg-blue-500/10 text-blue-400 border-blue-500/30 animate-pulse',
  partial: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
  failed: 'bg-red-500/10 text-red-400 border-red-500/30',
  pending: 'bg-slate-500/10 text-slate-400 border-slate-500/30',
};

export const AnalysisRunsList: React.FC<AnalysisRunsListProps> = ({ runs }) => {
  if (runs.length === 0) {
    return (
      <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-8 text-center text-slate-400">
        No code analysis runs recorded yet for this repository. Click "Run Code Analysis" to analyze source code.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl">
      <h3 className="mb-4 text-xl font-semibold text-slate-100">Analysis Runs History</h3>
      <table className="w-full text-left text-sm text-slate-300">
        <thead className="border-b border-slate-800 text-xs uppercase tracking-wider text-slate-400">
          <tr>
            <th className="pb-3 pt-2 font-semibold">Run ID</th>
            <th className="pb-3 pt-2 font-semibold">Status</th>
            <th className="pb-3 pt-2 font-semibold">Discovered</th>
            <th className="pb-3 pt-2 font-semibold">Analyzed</th>
            <th className="pb-3 pt-2 font-semibold">Entities</th>
            <th className="pb-3 pt-2 font-semibold">Relationships</th>
            <th className="pb-3 pt-2 font-semibold">Started At</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
          {runs.map((run) => (
            <tr key={run.id} className="hover:bg-slate-800/40">
              <td className="py-3 font-semibold text-slate-200">{run.id.substring(0, 8)}…</td>
              <td className="py-3">
                <span
                  className={`inline-block rounded-full border px-2.5 py-0.5 text-[11px] font-semibold uppercase ${
                    STATUS_BADGES[run.status] || STATUS_BADGES.pending
                  }`}
                >
                  {run.status}
                </span>
              </td>
              <td className="py-3 text-slate-300">{run.files_discovered} files</td>
              <td className="py-3 text-slate-300">{run.files_analyzed} files</td>
              <td className="py-3 text-emerald-400">{run.entities_found}</td>
              <td className="py-3 text-cyan-400">{run.relationships_found}</td>
              <td className="py-3 text-slate-400">{new Date(run.started_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
