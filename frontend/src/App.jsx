import { useRef, useState } from 'react'
import Logo from './components/Logo'
import ChatMessage from './components/ChatMessage'
import ChatInput from './components/ChatInput'
import ThemeToggle from './components/ThemeToggle'

async function askBackend(question, history) {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      history: history.map(({ role, text }) => ({ role, text })),
    }),
  })
  if (!res.ok) throw new Error('Request failed')
  return res.json()
}

function App() {
  const [messages, setMessages] = useState([])
  const [thinking, setThinking] = useState(false)
  const [previewThinking, setPreviewThinking] = useState(false)
  const bottomRef = useRef(null)

  async function handleSend(question) {
    const history = messages
    setMessages((prev) => [...prev, { role: 'user', text: question }])
    setThinking(true)

    try {
      const data = await askBackend(question, history)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: data.answer,
          sources: data.sources,
          confidence: data.confidence,
        },
      ])
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: "Something went wrong reaching the backend — is it running?" },
      ])
    } finally {
      setThinking(false)
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
    }
  }

  const hasStarted = messages.length > 0

  return (
    <div className="flex min-h-screen flex-col bg-paper">
      <header className="flex items-center justify-between px-6 py-5">
        <div className="flex items-center gap-3">
          <Logo size={43} />
          <span className="text-xl font-semibold tracking-wide text-slate-700 dark:text-slate-200">
            InvestED
          </span>
        </div>
        <ThemeToggle />
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-6">
        {!hasStarted ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-8 pb-24">
            <Logo size={90} thinking={thinking || previewThinking} />
            <div className="text-center">
              <h1 className="text-2xl font-semibold text-slate-800 dark:text-slate-100">
                What do you want to understand?
              </h1>
              <p className="mt-2 text-slate-400 dark:text-slate-500">
                Ask about investing, retirement accounts, credit, or taxes — grounded in real sources.
              </p>
            </div>
            <div className="w-full max-w-xl">
              <ChatInput onSend={handleSend} disabled={thinking} />
            </div>
            <button
              type="button"
              onClick={() => setPreviewThinking((v) => !v)}
              className="text-xs text-slate-300 transition-colors hover:text-slate-400"
            >
              {previewThinking ? 'stop' : 'preview'} thinking animation (dev)
            </button>
          </div>
        ) : (
          <>
            <div className="flex flex-1 flex-col gap-6 py-8">
              {messages.map((m, i) => (
                <ChatMessage key={i} {...m} />
              ))}
              {thinking && (
                <div className="flex justify-start px-1">
                  <Logo size={50} thinking />
                </div>
              )}
              <div ref={bottomRef} />
            </div>
            <div className="sticky bottom-0 bg-paper py-4">
              <ChatInput onSend={handleSend} disabled={thinking} />
            </div>
          </>
        )}
      </main>
    </div>
  )
}

export default App
