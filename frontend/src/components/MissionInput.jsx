import { useState } from 'react'

function MissionInput({ onSubmit, isLoading = false }) {
  const [goal, setGoal] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [maxResults, setMaxResults] = useState(10)
  const [formats, setFormats] = useState(['json', 'csv'])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!goal.trim() || !apiKey.trim() || isLoading) return

    const request = {
      goal: goal.trim(),
      api_key: apiKey.trim() || null,
      criteria: {
        required_fields: ['name', 'description'],
        quality_threshold: 0.7,
        max_results: maxResults
      },
      actions: {
        export_formats: formats
      },
      settings: {
        max_duration_hours: 4,
        checkpoint_interval_minutes: 15
      }
    }

    await onSubmit(request)
  }

  const toggleFormat = (format) => {
    setFormats(prev =>
      prev.includes(format)
        ? prev.filter(f => f !== format)
        : [...prev, format]
    )
  }

  const examples = [
    "Find 10 AI startups in healthcare that raised Series A-B in 2024-2025",
    "Research the top 5 competitors in the project management software space",
    "Identify emerging trends in sustainable packaging for food delivery"
  ]

  return (
    <div className="card p-8">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold mb-2 bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
          Start Your Research Mission
        </h2>
        <p className="text-slate-400">
          Describe your research goal and CHRONICLE will autonomously research,
          analyze, and deliver actionable results.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Goal Input */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Research Goal
          </label>
          <textarea
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="Describe what you want to research..."
            className="input min-h-[120px] resize-none"
            required
          />
          <div className="mt-2 flex flex-wrap gap-2">
            {examples.map((example, i) => (
              <button
                key={i}
                type="button"
                onClick={() => setGoal(example)}
                className="text-xs text-indigo-400 hover:text-indigo-300 hover:underline"
              >
                "{example.slice(0, 40)}..."
              </button>
            ))}
          </div>
        </div>

        {/* API Key Input */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Gemini API Key <span className="text-slate-500 font-normal">(required)</span>
          </label>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="AIza..."
            className="input"
            required
          />
          <p className="mt-1 text-xs text-slate-500">
            Get your free key at{' '}
            <a
              href="https://aistudio.google.com/apikey"
              target="_blank"
              rel="noopener noreferrer"
              className="text-indigo-400 hover:underline"
            >
              aistudio.google.com/apikey
            </a>
          </p>
        </div>

        {/* Settings */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Target Results
            </label>
            <select
              value={maxResults}
              onChange={(e) => setMaxResults(Number(e.target.value))}
              className="input"
            >
              <option value={5}>5 results</option>
              <option value={10}>10 results</option>
              <option value={20}>20 results</option>
              <option value={50}>50 results</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Export Formats
            </label>
            <div className="flex gap-2">
              {['json', 'csv', 'md', 'pdf'].map(format => (
                <button
                  key={format}
                  type="button"
                  onClick={() => toggleFormat(format)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    formats.includes(format)
                      ? 'bg-indigo-600 text-white'
                      : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                  }`}
                >
                  {format.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={!goal.trim() || !apiKey.trim() || isLoading}
          className="w-full btn-primary py-3 text-lg flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Starting Mission...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Start Research Mission
            </>
          )}
        </button>
      </form>

      {/* Features */}
      <div className="mt-8 pt-8 border-t border-slate-700">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-2xl mb-1">🔄</div>
            <div className="text-sm font-medium text-slate-300">Self-Correcting</div>
            <div className="text-xs text-slate-500">Auto re-researches gaps</div>
          </div>
          <div>
            <div className="text-2xl mb-1">⏸️</div>
            <div className="text-sm font-medium text-slate-300">Marathon Ready</div>
            <div className="text-xs text-slate-500">Pause & resume anytime</div>
          </div>
          <div>
            <div className="text-2xl mb-1">📊</div>
            <div className="text-sm font-medium text-slate-300">Real Exports</div>
            <div className="text-xs text-slate-500">JSON, CSV, PDF, MD</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default MissionInput
