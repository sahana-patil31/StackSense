import { Link, useLocation } from 'react-router-dom';

export const Navbar = () => {
  const location = useLocation();
  const user = JSON.parse(localStorage.getItem('stacksense_user') || 'null') as { email?: string; role?: string } | null;

  const isCurrent = (path: string) => location.pathname === path;

  return (
    <nav className="dashboard-nav sticky top-0 z-50 border-b border-slate-800 bg-slate-900/80 px-4 py-4 backdrop-blur-md sm:px-6">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex min-w-0 items-center gap-3">
          <Link to="/" className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-cyan-500/20 text-cyan-400 font-bold border border-cyan-500/40">
              S
            </span>
            <span className="text-xl font-bold tracking-wider text-slate-100">STACKSENSE</span>
          </Link>
        </div>

        <div className="flex min-w-0 flex-wrap items-center justify-start gap-x-4 gap-y-2 text-sm font-medium md:justify-end">
          <Link
            to="/"
            className={`transition-colors hover:text-cyan-400 ${
              isCurrent('/') ? 'text-cyan-400 font-semibold' : 'text-slate-400'
            }`}
          >
            Overview
          </Link>
          <Link
            to="/repositories"
            className={`transition-colors hover:text-cyan-400 ${
              isCurrent('/repositories') ? 'text-cyan-400 font-semibold' : 'text-slate-400'
            }`}
          >
            Repositories
          </Link>
          <Link
            to="/code-intelligence"
            className={`transition-colors hover:text-cyan-400 ${
              isCurrent('/code-intelligence') ? 'text-cyan-400 font-semibold' : 'text-slate-400'
            }`}
          >
            Code Intelligence
          </Link>
          <Link
            to="/risk"
            className={`transition-colors hover:text-cyan-400 ${
              isCurrent('/risk') ? 'text-cyan-400 font-semibold' : 'text-slate-400'
            }`}
          >
            Deployment Risk
          </Link>
          <Link
            to="/anomalies"
            className={`transition-colors hover:text-cyan-400 ${
              isCurrent('/anomalies') ? 'text-cyan-400 font-semibold' : 'text-slate-400'
            }`}
          >
            Anomalies
          </Link>
          <Link
            to="/incidents"
            className={`transition-colors hover:text-cyan-400 ${
              isCurrent('/incidents') ? 'text-cyan-400 font-semibold' : 'text-slate-400'
            }`}
          >
            Incidents
          </Link>
          <Link
            to="/settings"
            className={`transition-colors hover:text-cyan-400 ${
              isCurrent('/settings') ? 'text-cyan-400 font-semibold' : 'text-slate-400'
            }`}
          >
            Settings
          </Link>
          <Link
            to="/assistant"
            className={`transition-colors hover:text-cyan-400 ${
              isCurrent('/assistant') ? 'text-cyan-400 font-semibold' : 'text-slate-400'
            }`}
          >
            Assistant
          </Link>
          <span className="hidden border-l border-slate-700 pl-5 text-xs text-slate-500 sm:inline">{user?.role || 'USER'}</span>
          <button
            type="button"
            onClick={() => { localStorage.removeItem('stacksense_token'); localStorage.removeItem('stacksense_user'); window.location.href = '/'; }}
            className="text-slate-500 transition hover:text-red-300"
          >
            Sign out
          </button>
        </div>
      </div>
    </nav>
  );
};
