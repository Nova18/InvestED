import { useEffect, useState } from 'react'

function App() {
  const [apiStatus, setApiStatus] = useState('checking...')

  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json())
      .then((data) => setApiStatus(data.status))
      .catch(() => setApiStatus('unreachable (is the backend running?)'))
  }, [])

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-2 bg-white text-slate-900">
      <h1 className="text-4xl font-semibold">InvestED</h1>
      <p className="text-slate-500">backend: {apiStatus}</p>
    </div>
  )
}

export default App
