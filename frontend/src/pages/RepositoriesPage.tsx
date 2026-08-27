import { FormEvent, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { createRepository, fetchRepositories } from '../services/ingestion';
import type { Repository } from '../types/ingestion';

export const RepositoriesPage = () => {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [name, setName] = useState('');
  const [provider, setProvider] = useState('github');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const load = async () => { try { setRepositories(await fetchRepositories()); } catch { setError('Unable to load repositories.'); } finally { setLoading(false); } };
  useEffect(() => { void load(); }, []);
  const submit = async (event: FormEvent) => { event.preventDefault(); try { const item = await createRepository({ name, provider, default_branch: 'main' }); setRepositories((items) => [item, ...items]); setName(''); } catch (err: any) { setError(err?.response?.data?.detail || 'Unable to create repository.'); } };
  return <div className="min-h-screen bg-slate-950 text-slate-100"><Navbar /><main className="mx-auto max-w-6xl space-y-6 px-6 py-10"><header><p className="text-xs font-bold uppercase tracking-[0.25em] text-cyan-400">Workspace</p><h1 className="mt-2 text-3xl font-bold">Repositories</h1><p className="mt-2 text-sm text-slate-400">Manage the codebases used by analysis, risk, and assistant workflows.</p></header><form onSubmit={submit} className="flex flex-wrap gap-3 rounded-2xl border border-slate-800 bg-slate-900/70 p-5"><input required value={name} onChange={(event) => setName(event.target.value)} placeholder="Repository name" className="min-w-56 flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-cyan-400" /><select value={provider} onChange={(event) => setProvider(event.target.value)} className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"><option value="github">GitHub</option><option value="gitlab">GitLab</option><option value="local">Local</option><option value="other">Other</option></select><button className="rounded-lg bg-cyan-400 px-4 py-2 text-sm font-bold text-slate-950">Add repository</button></form>{error && <p className="text-sm text-red-400">{error}</p>}<section className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70">{loading ? <p className="p-6 text-slate-500">Loading repositories...</p> : repositories.length === 0 ? <p className="p-6 text-slate-500">No repositories registered yet.</p> : repositories.map((repository) => <div key={repository.id} className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 p-5 last:border-0"><div><h2 className="font-semibold">{repository.name}</h2><p className="mt-1 text-xs uppercase tracking-wider text-slate-500">{repository.provider} · {repository.default_branch || 'No default branch'}</p></div><Link to="/code-intelligence" className="text-sm text-cyan-300 hover:text-cyan-200">Analyze code</Link></div>)}</section></main></div>;
};