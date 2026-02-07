function FindingsTable({ findings }) {
  if (!findings || findings.length === 0) {
    return (
      <div className="card p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          Research Findings
        </h3>
        <div className="text-center py-8 text-slate-400">
          <div className="text-4xl mb-2">🔍</div>
          <p>No findings yet. Research in progress...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="card overflow-hidden">
      <div className="p-4 border-b border-slate-700">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          Research Findings
          <span className="ml-auto badge badge-info">{findings.length}</span>
        </h3>
      </div>

      <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
        <table className="w-full">
          <thead className="bg-slate-700/50 sticky top-0">
            <tr>
              <th className="text-left p-3 text-sm font-medium text-slate-400">#</th>
              <th className="text-left p-3 text-sm font-medium text-slate-400">Name</th>
              <th className="text-left p-3 text-sm font-medium text-slate-400">Description</th>
              <th className="text-left p-3 text-sm font-medium text-slate-400">Quality</th>
              <th className="text-left p-3 text-sm font-medium text-slate-400">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {findings.map((finding, index) => (
              <tr key={finding.id || index} className="hover:bg-slate-700/30 transition-colors">
                <td className="p-3 text-slate-500">{index + 1}</td>
                <td className="p-3">
                  <div className="font-medium text-slate-200">
                    {finding.name || 'Unknown'}
                  </div>
                  {finding.corrected && (
                    <span className="text-xs text-orange-400">Re-researched</span>
                  )}
                </td>
                <td className="p-3 text-sm text-slate-400 max-w-xs truncate">
                  {finding.description || '-'}
                </td>
                <td className="p-3">
                  <QualityBadge score={finding.quality_score || 0} />
                </td>
                <td className="p-3">
                  {finding.verified ? (
                    <span className="badge badge-success">Verified</span>
                  ) : finding.error ? (
                    <span className="badge badge-error">Error</span>
                  ) : (
                    <span className="badge badge-warning">Pending</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function QualityBadge({ score }) {
  const percentage = Math.round(score * 100)
  let colorClass = 'text-red-400'

  if (percentage >= 80) colorClass = 'text-green-400'
  else if (percentage >= 60) colorClass = 'text-yellow-400'
  else if (percentage >= 40) colorClass = 'text-orange-400'

  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-2 bg-slate-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${
            percentage >= 80 ? 'bg-green-500' :
            percentage >= 60 ? 'bg-yellow-500' :
            percentage >= 40 ? 'bg-orange-500' : 'bg-red-500'
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className={`text-sm font-medium ${colorClass}`}>{percentage}%</span>
    </div>
  )
}

export default FindingsTable
