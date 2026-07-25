import { useState } from 'react'

export default function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-center gap-3 rounded-full border border-mist bg-white px-5 py-3 shadow-sm transition-shadow focus-within:shadow-md"
    >
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Ask about investing, retirement, credit..."
        className="flex-1 bg-transparent text-slate-800 placeholder:text-slate-400 focus:outline-none"
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="rounded-full bg-ink px-4 py-1.5 text-sm text-white transition-opacity disabled:opacity-30"
      >
        Ask
      </button>
    </form>
  )
}
