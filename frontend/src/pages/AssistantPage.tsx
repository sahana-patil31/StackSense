import { FormEvent, useEffect, useState } from 'react';
import { Navbar } from '../components/Navbar';
import { chatWithAssistant } from '../services/assistant';
import { fetchRepositories } from '../services/ingestion';
import type { AssistantMessage, AssistantSource } from '../types/assistant';
import type { Repository } from '../types/ingestion';

const starterQuestions = [
  'What changed in the latest deployment?',
  'What functions call validate_token?',
  'Have we seen a similar payment failure?',
];

const sourceLabel = (source: AssistantSource) =>
  `${source.source_type.replace('_', ' ')}${source.source_id ? ` #${source.source_id.slice(0, 8)}` : ''}`;

export const AssistantPage = () => {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [repositoryId, setRepositoryId] = useState('');
  const [conversationId, setConversationId] = useState<string>();
  const [messages, setMessages] = useState<AssistantMessage[]>([]);
  const [question, setQuestion] = useState('');
  const [selectedSource, setSelectedSource] = useState<AssistantSource | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingRepositories, setLoadingRepositories] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadRepositories = async () => {
      try {
        const items = await fetchRepositories();
        setRepositories(items);
        if (items.length > 0) setRepositoryId(items[0].id);
      } catch {
        setError('Repositories could not be loaded. Check that the API is running.');
      } finally {
        setLoadingRepositories(false);
      }
    };
    void loadRepositories();
  }, []);

  const submitQuestion = async (event?: FormEvent) => {
    event?.preventDefault();
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || !repositoryId || loading) return;

    setLoading(true);
    setError(null);
    setMessages((current) => [...current, { role: 'user', content: trimmedQuestion }]);
    setQuestion('');
    try {
      const response = await chatWithAssistant(trimmedQuestion, repositoryId, conversationId);
      setConversationId(response.conversation_id);
      setMessages((current) => [
        ...current,
        { role: 'assistant', content: response.answer, sources: response.sources },
      ]);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'The assistant could not answer right now.');
    } finally {
      setLoading(false);
    }
  };

  const startNewConversation = () => {
    setConversationId(undefined);
    setMessages([]);
    setSelectedSource(null);
    setError(null);
  };

  const selectedRepository = repositories.find((item) => item.id === repositoryId);

  return (
    <div className="app-shell min-h-screen bg-[#E8DCC8] text-[#3B3025] font-sans">
      <Navbar />
      <main className="mx-auto max-w-7xl px-6 py-8">
        <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="mb-2 text-xs font-bold uppercase tracking-[0.25em] text-cyan-400">Engineering intelligence</p>
            <h1 className="text-3xl font-bold sm:text-4xl">Ask your system</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-400">
              Answers are grounded in indexed code, deployments, incidents, and dependencies for the selected repository.
            </p>
          </div>
          <button
            type="button"
            onClick={startNewConversation}
            className="rounded-xl border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:border-cyan-400 hover:text-cyan-300"
          >
            New conversation
          </button>
        </header>

        <section className="grid min-h-[620px] gap-px overflow-hidden rounded-2xl border border-slate-800 bg-slate-800 lg:grid-cols-[220px_minmax(0,1fr)_280px]">
          <aside className="bg-slate-900/95 p-4">
            <div className="mb-6">
              <label className="mb-2 block text-[11px] font-bold uppercase tracking-wider text-slate-500" htmlFor="repository">
                Repository scope
              </label>
              <select
                id="repository"
                value={repositoryId}
                disabled={loadingRepositories}
                onChange={(event) => {
                  setRepositoryId(event.target.value);
                  startNewConversation();
                }}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200 outline-none focus:border-cyan-400"
              >
                <option value="">Select repository</option>
                {repositories.map((repository) => (
                  <option key={repository.id} value={repository.id}>{repository.name}</option>
                ))}
              </select>
            </div>
            <p className="mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-500">Conversations</p>
            <button type="button" className="w-full rounded-lg bg-cyan-500/10 px-3 py-3 text-left text-sm text-cyan-300">
              {messages.length > 0 ? messages.find((message) => message.role === 'user')?.content.slice(0, 32) : 'New investigation'}
            </button>
          </aside>

          <section className="flex min-w-0 flex-col bg-slate-950/80">
            <div className="flex-1 space-y-5 overflow-y-auto p-5 sm:p-8">
              {messages.length === 0 && (
                <div className="mx-auto max-w-2xl py-14 text-center">
                  <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl border border-cyan-400/30 bg-cyan-400/10 text-2xl text-cyan-300">S</div>
                  <h2 className="text-xl font-semibold">What are you investigating?</h2>
                  <p className="mt-2 text-sm text-slate-400">Choose a repository, then ask about the evidence behind your system.</p>
                  <div className="mt-8 grid gap-2 text-left sm:grid-cols-3">
                    {starterQuestions.map((starter) => (
                      <button key={starter} type="button" onClick={() => setQuestion(starter)} className="rounded-xl border border-slate-800 bg-slate-900 p-3 text-xs text-slate-300 transition hover:border-cyan-400/60 hover:text-cyan-200">{starter}</button>
                    ))}
                  </div>
                </div>
              )}
              {messages.map((message, index) => (
                <article key={`${message.role}-${index}`} className={message.role === 'user' ? 'ml-auto max-w-2xl' : 'max-w-3xl'}>
                  <p className="mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-500">{message.role === 'user' ? 'You' : 'STACKSENSE'}</p>
                  <div className={message.role === 'user' ? 'rounded-2xl rounded-tr-sm bg-cyan-500 px-4 py-3 text-sm font-medium text-slate-950' : 'rounded-2xl rounded-tl-sm border border-slate-800 bg-slate-900 px-4 py-4 text-sm leading-6 text-slate-200'}>
                    {message.content}
                  </div>
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {message.sources.map((source) => (
                        <button key={`${source.source_type}-${source.source_id}-${source.title}`} type="button" onClick={() => setSelectedSource(source)} className="rounded-full border border-slate-700 px-3 py-1 text-xs text-cyan-300 transition hover:border-cyan-400 hover:bg-cyan-400/10">{sourceLabel(source)}</button>
                      ))}
                    </div>
                  )}
                </article>
              ))}
              {loading && <p className="text-sm text-slate-500">Searching indexed evidence...</p>}
            </div>
            <form onSubmit={submitQuestion} className="border-t border-slate-800 p-4 sm:p-5">
              {error && <p className="mb-3 text-sm text-red-400">{error}</p>}
              <div className="flex items-end gap-3 rounded-xl border border-slate-700 bg-slate-900 p-2 focus-within:border-cyan-400">
                <textarea value={question} onChange={(event) => setQuestion(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); void submitQuestion(); } }} placeholder={selectedRepository ? `Ask about ${selectedRepository.name}...` : 'Select a repository to begin...'} disabled={!repositoryId || loading} rows={2} className="min-h-12 flex-1 resize-none bg-transparent px-2 py-1 text-sm text-slate-100 outline-none placeholder:text-slate-600 disabled:cursor-not-allowed" />
                <button type="submit" disabled={!question.trim() || !repositoryId || loading} className="rounded-lg bg-cyan-400 px-4 py-2 text-sm font-bold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-40">Send</button>
              </div>
              <p className="mt-2 text-[11px] text-slate-600">Grounded answers only. Evidence and uncertainty are shown with each response.</p>
            </form>
          </section>

          <aside className="border-t border-slate-800 bg-slate-900/95 p-5 lg:border-l lg:border-t-0">
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Evidence</p>
            {selectedSource ? (
              <div className="mt-5">
                <p className="text-xs uppercase tracking-wider text-cyan-400">{sourceLabel(selectedSource)}</p>
                <h2 className="mt-3 text-lg font-semibold text-slate-100">{selectedSource.title}</h2>
                <dl className="mt-6 space-y-4 text-sm">
                  <div><dt className="text-slate-500">Source type</dt><dd className="mt-1 text-slate-200">{selectedSource.source_type}</dd></div>
                  <div><dt className="text-slate-500">Source ID</dt><dd className="mt-1 break-all font-mono text-xs text-slate-300">{selectedSource.source_id || 'Not assigned'}</dd></div>
                </dl>
              </div>
            ) : (
              <p className="mt-5 text-sm leading-6 text-slate-500">Click a source reference in an answer to inspect its identity.</p>
            )}
          </aside>
        </section>
      </main>
    </div>
  );
};