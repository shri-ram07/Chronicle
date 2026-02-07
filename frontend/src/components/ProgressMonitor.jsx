function ProgressMonitor({ status, mission }) {
  const state = status?.status || status?.state || 'pending'
  const progress = status?.progress || {}

  // Handle both SSE progress format (completed/total) and polling status format (findings_count/target_count)
  const findingsCount = progress.findings_count ?? progress.completed ?? 0
  const targetCount = progress.target_count ?? progress.total ?? 10
  const currentPhase = progress.current_phase ?? progress.phase ?? state

  const stateColors = {
    pending: 'text-slate-400',
    planning: 'text-blue-400',
    researching: 'text-indigo-400',
    analyzing: 'text-purple-400',
    scoring: 'text-pink-400',
    correcting: 'text-orange-400',
    exporting: 'text-green-400',
    paused: 'text-yellow-400',
    completed: 'text-green-400',
    failed: 'text-red-400'
  }

  const stateIcons = {
    pending: '⏳',
    planning: '📋',
    researching: '🔍',
    analyzing: '🧠',
    scoring: '⭐',
    correcting: '🔄',
    exporting: '📤',
    paused: '⏸️',
    completed: '✅',
    failed: '❌'
  }

  // Use SSE percentage if available, otherwise calculate
  const percentage = progress.percentage ?? (
    targetCount > 0 ? Math.round((findingsCount / targetCount) * 100) : 0
  )

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        Mission Progress
      </h3>

      {/* State Badge */}
      <div className="flex items-center gap-3 mb-6">
        <span className="text-2xl">{stateIcons[state] || '⏳'}</span>
        <div>
          <div className={`text-lg font-semibold capitalize ${stateColors[state]}`}>
            {state.replace('_', ' ')}
          </div>
          <div className="text-sm text-slate-400">
            {status?.current_activity || 'Initializing...'}
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-slate-400">Findings</span>
          <span className="text-slate-300">
            {findingsCount} / {targetCount}
          </span>
        </div>
        <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-500"
            style={{ width: `${Math.min(percentage, 100)}%` }}
          />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-slate-700/50 rounded-lg p-3">
          <div className="text-2xl font-bold text-indigo-400">
            {(progress.quality_average || 0).toFixed(2)}
          </div>
          <div className="text-xs text-slate-400">Avg Quality</div>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-3">
          <div className="text-2xl font-bold text-orange-400">
            {progress.corrections_made || 0}
          </div>
          <div className="text-xs text-slate-400">Corrections</div>
        </div>
      </div>

      {/* Mission ID */}
      <div className="mt-4 pt-4 border-t border-slate-700">
        <div className="text-xs text-slate-500">
          Mission ID: <code className="text-slate-400">{mission?.mission_id}</code>
        </div>
      </div>
    </div>
  )
}

export default ProgressMonitor
