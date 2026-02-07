import { useState } from 'react'

function ExportPanel({ exports, onExport, missionId }) {
  const [isExporting, setIsExporting] = useState(false)

  const handleExport = async (formats) => {
    setIsExporting(true)
    await onExport(formats)
    setIsExporting(false)
  }

  const formatIcons = {
    json: '{ }',
    csv: '📊',
    md: '📝',
    markdown: '📝',
    pdf: '📄'
  }

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
        </svg>
        Exports
      </h3>

      {/* Quick Export Buttons */}
      <div className="flex flex-wrap gap-2 mb-4">
        <button
          onClick={() => handleExport(['json'])}
          disabled={isExporting}
          className="btn-secondary text-sm flex items-center gap-1"
        >
          <span>{ }</span> JSON
        </button>
        <button
          onClick={() => handleExport(['csv'])}
          disabled={isExporting}
          className="btn-secondary text-sm flex items-center gap-1"
        >
          <span>📊</span> CSV
        </button>
        <button
          onClick={() => handleExport(['md'])}
          disabled={isExporting}
          className="btn-secondary text-sm flex items-center gap-1"
        >
          <span>📝</span> Markdown
        </button>
        <button
          onClick={() => handleExport(['pdf'])}
          disabled={isExporting}
          className="btn-secondary text-sm flex items-center gap-1"
        >
          <span>📄</span> PDF
        </button>
        <button
          onClick={() => handleExport(['json', 'csv', 'md', 'pdf'])}
          disabled={isExporting}
          className="btn-primary text-sm"
        >
          Export All
        </button>
      </div>

      {/* Export List */}
      {exports && exports.length > 0 ? (
        <div className="space-y-2">
          {exports.map((exp, index) => (
            <div
              key={exp.id || index}
              className={`flex items-center justify-between p-3 rounded-lg ${
                exp.status === 'success' ? 'bg-green-900/20 border border-green-800' :
                exp.status === 'failed' ? 'bg-red-900/20 border border-red-800' :
                'bg-slate-700/50'
              }`}
            >
              <div className="flex items-center gap-3">
                <span className="text-xl">{formatIcons[exp.format] || '📁'}</span>
                <div>
                  <div className="font-medium text-slate-200 uppercase text-sm">
                    {exp.format}
                  </div>
                  {exp.records_exported && (
                    <div className="text-xs text-slate-400">
                      {exp.records_exported} records
                    </div>
                  )}
                </div>
              </div>

              {exp.status === 'success' && exp.file_url && (
                <a
                  href={exp.file_url}
                  download
                  className="btn-primary text-xs py-1 px-3"
                >
                  Download
                </a>
              )}

              {exp.status === 'failed' && (
                <span className="text-xs text-red-400">{exp.error}</span>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-4 text-slate-500">
          <div className="text-2xl mb-2">📁</div>
          <p className="text-sm">No exports yet</p>
        </div>
      )}
    </div>
  )
}

export default ExportPanel
