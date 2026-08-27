import { FormEvent, useState } from 'react';
import { login, register } from '../services/auth';
import type { AuthResponse } from '../types/auth';

interface LoginPageProps { onAuthenticated: (response: AuthResponse) => void; }

export const LoginPage = ({ onAuthenticated }: LoginPageProps) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      onAuthenticated(creating ? await register(email, password) : await login(email, password));
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Authentication failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="app-shell flex min-h-screen items-center justify-center bg-[#E8DCC8] px-6 py-12 text-[#3B3025]">
      <section className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-8 shadow-2xl">
        <div className="mb-8 flex items-center gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#8B6F47] font-bold text-white">S</span><div><p className="font-bold tracking-widest">STACKSENSE</p><p className="text-xs text-[#6B5B4A]">Engineering intelligence</p></div></div>
        <h1 className="text-2xl font-semibold">{creating ? 'Create your account' : 'Welcome back'}</h1>
        <p className="mt-2 text-sm text-[#6B5B4A]">Secure access to your engineering workspace.</p>
        <form onSubmit={submit} className="mt-7 space-y-4">
          <label className="block text-sm text-[#3B3025]">Email<input required type="email" value={email} onChange={(event) => setEmail(event.target.value)} className="login-input mt-2 w-full rounded-lg border border-[#C5AD8A] bg-white px-3 py-2.5 text-[#2F241C] outline-none placeholder:text-[#5A4939] focus:border-[#6F5638]" /></label>
          <label className="block text-sm text-[#3B3025]">Password<input required minLength={8} type="password" value={password} onChange={(event) => setPassword(event.target.value)} className="login-input mt-2 w-full rounded-lg border border-[#C5AD8A] bg-white px-3 py-2.5 text-[#2F241C] outline-none placeholder:text-[#5A4939] focus:border-[#6F5638]" /></label>
          {error && <p className="text-sm text-[#B42318]">{error}</p>}
          <button disabled={loading} className="w-full rounded-lg bg-[#4A3829] px-4 py-2.5 font-semibold text-white transition hover:bg-[#6F5638] disabled:opacity-50">{loading ? 'Working...' : creating ? 'Create account' : 'Sign in'}</button>
        </form>
        <button type="button" onClick={() => { setCreating((value) => !value); setError(null); }} className="mt-5 text-sm text-[#8B6F47] hover:text-[#6F5638]">{creating ? 'Already have an account? Sign in' : 'Need an account? Register'}</button>
      </section>
    </main>
  );
};