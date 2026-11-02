import { useEffect, useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'

type DocumentInfo = {
  doc_id: string
  file_name: string
  collection_name: string
  uploaded_at: string
  mime_type: string
}

type Citation = {
  document_id: string
  document_name: string
  page: number | null
  snippet: string
  score: number
}

type ChatResponse = {
  answer: string
  citations: Citation[]
  intent: string
  abstained: boolean
  evidence_count: number
  latency_ms: number
  debug?: Record<string, unknown>
}

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api'

export default function App() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([])
  const [question, setQuestion] = useState('What is the remote work policy?')
  const [answer, setAnswer] = useState<ChatResponse | null>(null)
  const [loadingDocuments, setLoadingDocuments] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [loadingAnswer, setLoadingAnswer] = useState(false)

  const loadDocuments = async () => {
    setLoadingDocuments(true)
    try {
      const response = await fetch(`${API_BASE}/documents`)
      if (!response.ok) {
        throw new Error('Unable to load documents')
      }
      const payload = await response.json()
      setDocuments(payload.documents ?? [])
    } catch (error) {
      console.error(error)
    } finally {
      setLoadingDocuments(false)
    }
  }

  useEffect(() => {
    void loadDocuments()
  }, [])

  const handleUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files || files.length === 0) {
      return
    }

    const formData = new FormData()
    Array.from(files).forEach((file) => formData.append('files', file))

    setUploading(true)
    try {
      const response = await fetch(`${API_BASE}/documents/upload`, {
        method: 'POST',
        body: formData,
      })
      if (!response.ok) {
        throw new Error('Upload failed')
      }
      setQuestion((current) => current || 'What is the remote work policy?')
      await loadDocuments()
    } catch (error) {
      console.error(error)
    } finally {
      setUploading(false)
      event.target.value = ''
    }
  }

  const handleAsk = async (event: FormEvent) => {
    event.preventDefault()
    if (!question.trim()) {
      return
    }

    setLoadingAnswer(true)
    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, top_k: 5 }),
      })
      if (!response.ok) {
        throw new Error('Unable to get answer')
      }
      const payload: ChatResponse = await response.json()
      setAnswer(payload)
    } catch (error) {
      console.error(error)
    } finally {
      setLoadingAnswer(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <header className="mb-8 rounded-2xl border border-sky-500/30 bg-slate-900/80 p-6 shadow-2xl shadow-sky-900/20 backdrop-blur">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm font-medium uppercase tracking-[0.2em] text-sky-300">Enterprise AI</p>
              <h1 className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">IntelliDocs AI</h1>
            </div>
            <label className="inline-flex cursor-pointer items-center justify-center rounded-xl bg-sky-500 px-4 py-2 font-medium text-slate-950 transition hover:bg-sky-400">
              {uploading ? 'Uploading…' : 'Upload documents'}
              <input className="hidden" type="file" multiple onChange={handleUpload} />
            </label>
          </div>
        </header>

        <main className="grid gap-6 lg:grid-cols-[1.1fr_2fr]">
          <aside className="rounded-2xl border border-slate-800 bg-slate-900/75 p-5 shadow-xl shadow-slate-900/40">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-100">Knowledge base</h2>
              <span className="rounded-full border border-emerald-500/40 bg-emerald-500/10 px-2 py-1 text-xs text-emerald-300">
                {documents.length} files
              </span>
            </div>

            {loadingDocuments ? (
              <p className="text-sm text-slate-400">Loading document index…</p>
            ) : documents.length === 0 ? (
              <p className="text-sm text-slate-400">Upload PDFs, DOCX, or TXT files to begin.</p>
            ) : (
              <ul className="space-y-3">
                {documents.map((document) => (
                  <li key={document.doc_id} className="rounded-xl border border-slate-800 bg-slate-950/70 p-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-medium text-slate-100">{document.file_name}</p>
                        <p className="mt-1 text-xs text-slate-400">{document.mime_type}</p>
                      </div>
                      <span className="rounded-full bg-sky-500/10 px-2 py-1 text-[10px] uppercase tracking-wide text-sky-300">
                        {document.collection_name}
                      </span>
                    </div>
                    <p className="mt-2 text-xs text-slate-500">{new Date(document.uploaded_at).toLocaleString()}</p>
                  </li>
                ))}
              </ul>
            )}
          </aside>

          <section className="rounded-2xl border border-slate-800 bg-slate-900/75 p-5 shadow-xl shadow-slate-900/40">
            <h2 className="text-lg font-semibold text-slate-100">Ask the assistant</h2>
            <form className="mt-4 space-y-4" onSubmit={handleAsk}>
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                rows={4}
                className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-500/20"
                placeholder="Ask about your uploaded knowledge base"
              />
              <div className="flex items-center justify-between gap-3">
                <span className="text-xs text-slate-400">Grounded retrieval, reranking, and intent routing.</span>
                <button
                  type="submit"
                  disabled={loadingAnswer}
                  className="inline-flex items-center justify-center rounded-xl bg-violet-500 px-4 py-2 font-medium text-white transition hover:bg-violet-400 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loadingAnswer ? 'Thinking…' : 'Query knowledge base'}
                </button>
              </div>
            </form>

            <div className="mt-6 rounded-xl border border-slate-800 bg-slate-950/70 p-4">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-400">Answer</h3>
                {answer && (
                  <span className="rounded-full border border-sky-500/30 bg-sky-500/10 px-2 py-1 text-[10px] font-medium uppercase tracking-wide text-sky-300">
                    {answer.intent}
                  </span>
                )}
              </div>

              {answer ? (
                <>
                  <p className="whitespace-pre-line text-sm leading-7 text-slate-200">{answer.answer}</p>
                  <div className="mt-5 flex flex-wrap gap-2 text-xs text-slate-300">
                    <span className="rounded-full border border-slate-700 bg-slate-900 px-2 py-1">Evidence: {answer.evidence_count}</span>
                    <span className="rounded-full border border-slate-700 bg-slate-900 px-2 py-1">Latency: {answer.latency_ms} ms</span>
                    <span className="rounded-full border border-slate-700 bg-slate-900 px-2 py-1">Abstained: {answer.abstained ? 'Yes' : 'No'}</span>
                  </div>

                  {answer.citations.length > 0 && (
                    <div className="mt-5 space-y-3 border-t border-slate-800 pt-4">
                      <h4 className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Citations</h4>
                      {answer.citations.map((citation, index) => (
                        <div key={`${citation.document_id}-${index}`} className="rounded-xl border border-slate-800 bg-slate-900 p-3">
                          <div className="mb-1 flex items-center justify-between gap-3">
                            <p className="text-sm font-medium text-sky-300">{citation.document_name}</p>
                            <span className="text-[10px] uppercase tracking-wide text-slate-400">score {citation.score.toFixed(3)}</span>
                          </div>
                          <p className="text-xs text-slate-400">Page {citation.page ?? 'N/A'}</p>
                          <p className="mt-2 text-sm leading-6 text-slate-200">{citation.snippet}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <p className="text-sm text-slate-400">Submit a question to see the grounded response here.</p>
              )}
            </div>
          </section>
        </main>
      </div>
    </div>
  )
}
