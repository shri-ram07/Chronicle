import { useState, useEffect, useCallback, useRef } from 'react'
import MissionInput from './components/MissionInput'
import ProgressMonitor from './components/ProgressMonitor'
import FindingsTable from './components/FindingsTable'
import ActivityFeed from './components/ActivityFeed'
import ExportPanel from './components/ExportPanel'

// API Base URL - uses environment variable in production, localhost in dev
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [mission, setMission] = useState(null)
  const [status, setStatus] = useState(null)
  const [findings, setFindings] = useState([])
  const [activities, setActivities] = useState([])
  const [exports, setExports] = useState([])
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const eventSourceRef = useRef(null)

  // Add activity to feed
  const addActivity = useCallback((type, message) => {
    setActivities(prev => [{
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type,
      message,
      timestamp: new Date().toISOString()
    }, ...prev].slice(0, 50))
  }, [])

  // Connect to SSE stream
  const connectToStream = useCallback((missionId) => {
    // Validate mission ID
    if (!missionId || missionId === 'undefined') {
      console.error('Invalid mission ID:', missionId)
      addActivity('error', 'Invalid mission ID - cannot connect to stream')
      return
    }

    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    const streamUrl = `${API_BASE}/api/status/${missionId}/stream`
    console.log('Connecting to SSE stream:', streamUrl)

    const eventSource = new EventSource(streamUrl)
    eventSourceRef.current = eventSource

    eventSource.onopen = () => {
      console.log('SSE connection opened')
      setIsConnected(true)
      setError(null)
      addActivity('info', 'Connected to mission stream')
    }

    eventSource.onerror = (e) => {
      console.error('SSE error:', e)
      setIsConnected(false)
      // Don't show error if we just completed
      if (status?.state !== 'completed') {
        addActivity('error', 'Stream connection lost - will retry via polling')
      }
    }

    eventSource.addEventListener('status', (e) => {
      try {
        const data = JSON.parse(e.data)
        setStatus(prev => ({ ...prev, ...data }))
        addActivity('status', data.activity || `State: ${data.state}`)
      } catch (err) {
        console.error('Failed to parse status event:', err)
      }
    })

    eventSource.addEventListener('progress', (e) => {
      try {
        const data = JSON.parse(e.data)
        setStatus(prev => ({ ...prev, progress: data }))
      } catch (err) {
        console.error('Failed to parse progress event:', err)
      }
    })

    eventSource.addEventListener('finding', (e) => {
      try {
        const finding = JSON.parse(e.data)
        setFindings(prev => [...prev, finding])
        addActivity('finding', `Found: ${finding.name || 'New finding'}`)
      } catch (err) {
        console.error('Failed to parse finding event:', err)
      }
    })

    eventSource.addEventListener('action', (e) => {
      try {
        const action = JSON.parse(e.data)
        setExports(prev => [...prev, action])
        addActivity('action', `Exported: ${action.format || action.action_type}`)
      } catch (err) {
        console.error('Failed to parse action event:', err)
      }
    })

    eventSource.addEventListener('complete', (e) => {
      try {
        const data = JSON.parse(e.data)
        setStatus(prev => ({ ...prev, state: 'completed' }))
        addActivity('complete', `Mission complete! ${data.findings_count || 0} findings`)
        eventSource.close()
        setIsConnected(false)
      } catch (err) {
        console.error('Failed to parse complete event:', err)
      }
    })

    eventSource.addEventListener('heartbeat', (e) => {
      console.log('Heartbeat received')
    })

    // Note: SSE 'error' events from server are different from connection errors
    eventSource.addEventListener('error', (e) => {
      try {
        if (e.data) {
          const data = JSON.parse(e.data)
          addActivity('error', data.error || 'Unknown error')
        }
      } catch (err) {
        // Not a JSON error event, might be connection error
        console.log('SSE error event (non-JSON):', e)
      }
    })

  }, [addActivity, status?.state])

  // Start a new mission
  const startMission = async (request) => {
    setIsLoading(true)
    setError(null)
    setActivities([])
    setFindings([])
    setExports([])
    setStatus(null)
    setMission(null)

    try {
      addActivity('info', 'Starting research mission...')

      const response = await fetch(`${API_BASE}/api/research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      })

      // Check if response is OK
      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Server error (${response.status}): ${errorText}`)
      }

      const data = await response.json()
      console.log('Mission created:', data)

      // Validate response has mission_id
      if (!data.mission_id) {
        throw new Error('Server did not return a mission ID')
      }

      setMission(data)
      addActivity('info', `Mission ${data.mission_id} created`)

      // Small delay to ensure backend is ready
      await new Promise(resolve => setTimeout(resolve, 500))

      // Start SSE connection
      connectToStream(data.mission_id)

    } catch (error) {
      console.error('Failed to start mission:', error)
      setError(error.message)
      addActivity('error', `Failed to start mission: ${error.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  // Pause mission
  const pauseMission = async () => {
    if (!mission?.mission_id) return
    try {
      const response = await fetch(`${API_BASE}/api/control/${mission.mission_id}/pause`, {
        method: 'POST'
      })
      if (!response.ok) {
        throw new Error(`Failed to pause: ${response.status}`)
      }
      addActivity('info', 'Mission paused')
      setStatus(prev => ({ ...prev, state: 'paused' }))
    } catch (error) {
      addActivity('error', `Failed to pause: ${error.message}`)
    }
  }

  // Resume mission
  const resumeMission = async () => {
    if (!mission?.mission_id) return
    try {
      const response = await fetch(`${API_BASE}/api/control/${mission.mission_id}/resume`, {
        method: 'POST'
      })
      if (!response.ok) {
        throw new Error(`Failed to resume: ${response.status}`)
      }
      addActivity('info', 'Mission resumed')
      connectToStream(mission.mission_id)
    } catch (error) {
      addActivity('error', `Failed to resume: ${error.message}`)
    }
  }

  // Export findings
  const exportFindings = async (formats) => {
    if (!mission?.mission_id) return
    try {
      const response = await fetch(`${API_BASE}/api/export/${mission.mission_id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ formats })
      })
      if (!response.ok) {
        throw new Error(`Export failed: ${response.status}`)
      }
      const data = await response.json()
      if (data.exports) {
        setExports(prev => [...prev, ...data.exports])
      }
      addActivity('action', `Exported to ${formats.join(', ')}`)
    } catch (error) {
      addActivity('error', `Export failed: ${error.message}`)
    }
  }

  // Reset to start new mission
  const resetMission = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }
    setMission(null)
    setStatus(null)
    setFindings([])
    setActivities([])
    setExports([])
    setIsConnected(false)
    setError(null)
  }

  // Poll for status updates as backup when SSE is not connected
  useEffect(() => {
    if (!mission?.mission_id) return
    if (isConnected) return // Don't poll if SSE is connected
    if (status?.state === 'completed') return // Don't poll if completed

    const pollStatus = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/status/${mission.mission_id}`)
        if (response.ok) {
          const data = await response.json()
          setStatus(data)
        }

        // Fetch findings
        const findingsRes = await fetch(`${API_BASE}/api/findings/${mission.mission_id}`)
        if (findingsRes.ok) {
          const findingsData = await findingsRes.json()
          setFindings(findingsData.findings || [])
        }
      } catch (error) {
        console.error('Status poll failed:', error)
      }
    }

    // Initial poll
    pollStatus()

    const interval = setInterval(pollStatus, 5000)
    return () => clearInterval(interval)
  }, [mission?.mission_id, isConnected, status?.state])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/chronicle.svg" alt="Chronicle" className="w-10 h-10" />
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                CHRONICLE
              </h1>
              <p className="text-xs text-slate-400">Marathon Research Agent</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {isConnected && (
              <div className="flex items-center gap-2 text-sm text-green-400">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                </span>
                Live
              </div>
            )}

            {mission && (
              <div className="flex gap-2">
                {status?.state === 'completed' ? (
                  <button onClick={resetMission} className="btn-primary text-sm">
                    New Mission
                  </button>
                ) : status?.state === 'paused' ? (
                  <button onClick={resumeMission} className="btn-primary text-sm">
                    Resume
                  </button>
                ) : (
                  <button onClick={pauseMission} className="btn-secondary text-sm">
                    Pause
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Error Banner */}
        {error && (
          <div className="mb-6 p-4 bg-red-900/50 border border-red-700 rounded-lg text-red-200">
            <div className="flex items-center gap-2">
              <span className="text-xl">⚠️</span>
              <span>{error}</span>
              <button
                onClick={() => setError(null)}
                className="ml-auto text-red-400 hover:text-red-300"
              >
                ✕
              </button>
            </div>
          </div>
        )}

        {!mission ? (
          // No mission - show input
          <div className="max-w-2xl mx-auto">
            <MissionInput onSubmit={startMission} isLoading={isLoading} />
          </div>
        ) : (
          // Mission in progress - show dashboard
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column - Progress & Activity */}
            <div className="lg:col-span-1 space-y-6">
              <ProgressMonitor status={status} mission={mission} />
              <ActivityFeed activities={activities} />
            </div>

            {/* Right Column - Findings & Exports */}
            <div className="lg:col-span-2 space-y-6">
              <FindingsTable findings={findings} />
              <ExportPanel
                exports={exports}
                onExport={exportFindings}
                missionId={mission.mission_id}
              />
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-700 mt-auto">
        <div className="max-w-7xl mx-auto px-4 py-4 text-center text-sm text-slate-500">
          Built with Google ADK & Gemini 3 Pro | Gemini Hackathon 2025
        </div>
      </footer>
    </div>
  )
}

export default App
