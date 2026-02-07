function ActivityFeed({ activities }) {
  const typeStyles = {
    status: { icon: '📊', color: 'text-blue-400' },
    finding: { icon: '🎯', color: 'text-green-400' },
    action: { icon: '📤', color: 'text-purple-400' },
    error: { icon: '❌', color: 'text-red-400' },
    info: { icon: 'ℹ️', color: 'text-slate-400' },
    complete: { icon: '✅', color: 'text-green-400' }
  }

  const formatTime = (timestamp) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    })
  }

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        Live Activity
        {activities.length > 0 && (
          <span className="relative flex h-2 w-2 ml-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
          </span>
        )}
      </h3>

      <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2">
        {activities.length === 0 ? (
          <div className="text-center py-4 text-slate-500">
            Waiting for activity...
          </div>
        ) : (
          activities.map((activity) => {
            const style = typeStyles[activity.type] || typeStyles.info
            return (
              <div
                key={activity.id}
                className="flex items-start gap-3 p-2 rounded-lg hover:bg-slate-700/30 transition-colors"
              >
                <span className="text-lg">{style.icon}</span>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm ${style.color} truncate`}>
                    {activity.message}
                  </p>
                  <p className="text-xs text-slate-500">
                    {formatTime(activity.timestamp)}
                  </p>
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

export default ActivityFeed
