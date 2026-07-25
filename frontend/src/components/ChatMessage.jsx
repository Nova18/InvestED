import { motion } from 'framer-motion'

function ConfidenceBar({ value }) {
  const pct = Math.round(value * 100)
  return (
    <div className="flex items-center gap-2 text-xs text-slate-400">
      <div className="h-1 w-16 overflow-hidden rounded-full bg-mist">
        <div
          className="h-full rounded-full bg-ink-light"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span>{pct}% confident</span>
    </div>
  )
}

export default function ChatMessage({ role, text, sources, confidence }) {
  const isUser = role === 'user'

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div className={`max-w-2xl ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-2`}>
        <div
          className={
            isUser
              ? 'rounded-2xl bg-mist px-4 py-2.5 text-slate-800'
              : 'px-1 text-slate-800 leading-relaxed'
          }
        >
          {text}
        </div>

        {!isUser && sources?.length > 0 && (
          <div className="flex flex-wrap gap-2 px-1">
            {sources.map((s) => (
              <a
                key={s.url ?? s.title}
                href={s.url ?? undefined}
                target="_blank"
                rel="noreferrer"
                className="rounded-full border border-mist px-3 py-1 text-xs text-slate-500 transition-colors hover:border-ink-light hover:text-ink-light"
              >
                {s.title}
              </a>
            ))}
          </div>
        )}

        {!isUser && typeof confidence === 'number' && (
          <div className="px-1">
            <ConfidenceBar value={confidence} />
          </div>
        )}
      </div>
    </motion.div>
  )
}
