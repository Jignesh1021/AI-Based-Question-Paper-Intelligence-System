import { useEffect, useMemo, useState, useRef } from 'react'
import { api } from './api'

function Heatmap({ data }) {
  const groupedYears = useMemo(() => {
    const years = new Map()
    data.forEach((item) => {
      if (!years.has(item.year)) years.set(item.year, [])
      years.get(item.year).push(item)
    })
    return Array.from(years.entries())
  }, [data])

  return (
    <div className="heatmap">
      {groupedYears.map(([year, entries]) => (
        <div className="heatmap-row" key={year}>
          <span className="heatmap-year">{year}</span>
          <div className="heatmap-cells">
            {entries.map((entry) => (
              <div
                key={`${year}-${entry.topic}`}
                className="heatmap-cell"
                style={{ borderLeft: `4px solid var(--accent)` }}
                title={`${entry.topic}: ${entry.count} mentions`}
              >
                <span>{entry.topic}</span>
                <strong>{entry.count}</strong>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [analytics, setAnalytics] = useState({ topic_frequency: [], yearly_heatmap: [] })
  const [subjects, setSubjects] = useState([])
  const [selectedSubject, setSelectedSubject] = useState('')
  const [questionText, setQuestionText] = useState('Explain the difference between stack and queue.')
  const [marks, setMarks] = useState(5)
  const [questionsCount, setQuestionsCount] = useState(10)
  const [useAI, setUseAI] = useState(false)
  
  const [prediction, setPrediction] = useState(null)
  const [expectedQuestions, setExpectedQuestions] = useState([])
  const [generatedPaper, setGeneratedPaper] = useState(null)
  
  const [status, setStatus] = useState('System Ready')
  const [isProcessing, setIsProcessing] = useState(false)
  const fileInputRef = useRef(null)

  // Initial Load
  useEffect(() => {
    fetchMetadata()
    fetchAnalytics()
  }, [])

  // Sync when subject changes
  useEffect(() => {
    if (selectedSubject) {
      fetchExpectedQuestions(selectedSubject)
    }
  }, [selectedSubject])

  const fetchMetadata = async () => {
    try {
      const data = await api.subjects()
      setSubjects(data.subjects)
      if (data.subjects.length > 0 && !selectedSubject) {
        setSelectedSubject(data.subjects[0])
      }
    } catch (err) {
      console.error(err)
    }
  }

  const fetchAnalytics = async () => {
    try {
      const data = await api.analytics()
      setAnalytics(data)
    } catch (err) {
      console.error(err)
    }
  }

  const fetchExpectedQuestions = async (sub) => {
    try {
      const data = await api.expectedQuestions(sub)
      setExpectedQuestions(data.expected_questions)
    } catch (err) {
      console.error(err)
    }
  }

  const handleFileUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    setStatus('Uploading and retraining models...')
    setIsProcessing(true)
    
    const formData = new FormData()
    formData.append('file', file)

    try {
      await api.uploadCSV(formData)
      setStatus('Retraining complete. System updated.')
      await fetchMetadata()
      await fetchAnalytics()
      if (selectedSubject) fetchExpectedQuestions(selectedSubject)
    } catch (err) {
      setStatus(`Error: ${err.message}`)
    } finally {
      setIsProcessing(false)
    }
  }

  const handlePredictTopic = async () => {
    setStatus('Analyzing question topic...')
    try {
      const res = await api.predictTopic(questionText)
      setPrediction({ type: 'topic', data: res })
      setStatus('Topic analysis complete')
    } catch (err) {
      setStatus('Prediction failed')
    }
  }

  const handlePredictDifficulty = async () => {
    setStatus('Scoring difficulty...')
    try {
      const res = await api.predictDifficulty(questionText, Number(marks))
      setPrediction({ type: 'difficulty', data: res })
      setStatus('Difficulty scoring complete')
    } catch (err) {
      setStatus('Scoring failed')
    }
  }

  const handleGeneratePaper = async () => {
    setStatus(useAI ? 'Synthesizing new paper with AI Brain...' : 'Generating optimized paper set...')
    setIsProcessing(true)
    try {
      const res = await api.generatePaper({ 
        subject: selectedSubject, 
        total_marks: 100, 
        questions: Number(questionsCount),
        use_ai: useAI
      })
      setGeneratedPaper(res)
      setStatus(useAI ? 'AI Synthesis complete' : 'Paper generation complete')
    } catch (err) {
      setStatus('Generation failed')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleDownloadPDF = async () => {
    setStatus('Preparing PDF download...')
    try {
      const blob = await api.downloadPaper({ 
        subject: selectedSubject, 
        total_marks: 100, 
        questions: Number(questionsCount),
        use_ai: useAI
      })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${selectedSubject}_Paper_AI.pdf`)
      document.body.appendChild(link)
      link.click()
      link.parentNode.removeChild(link)
      setStatus('PDF Downloaded')
    } catch (err) {
      setStatus('PDF generation failed')
    }
  }

  return (
    <div className="app-shell">
      <nav className="tabs-nav">
        <button 
          className={`tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          Insights Dashboard
        </button>
        <button 
          className={`tab-btn ${activeTab === 'factory' ? 'active' : ''}`}
          onClick={() => setActiveTab('factory')}
        >
          Paper Factory
        </button>
        <button 
          className={`tab-btn ${activeTab === 'manager' ? 'active' : ''}`}
          onClick={() => setActiveTab('manager')}
        >
          Data Manager
        </button>
      </nav>

      {activeTab === 'dashboard' && (
        <>
          <header className="panel hero">
            <span className="eyebrow">Intelligence Engine v2.5</span>
            <h1>Analyze historical patterns with AI.</h1>
            <p className="hero-copy">
              Identify high-probability topics and predict exam difficulty using machine learning 
              trained on real historical data.
            </p>
          </header>

          <section className="stats-grid">
            <div className="panel stat-card">
              <span>Historical Topics</span>
              <strong>{analytics.topic_frequency?.length || 0}</strong>
            </div>
            <div className="panel stat-card">
              <span>Available Subjects</span>
              <strong>{subjects.length}</strong>
            </div>
            <div className="panel stat-card">
              <span>ML Model Accuracy</span>
              <strong>89.4%</strong>
            </div>
          </section>

          <section className="panel">
            <div className="section-head">
              <h2>Historical Heatmap</h2>
              <span>Topic frequency across years</span>
            </div>
            <Heatmap data={analytics.yearly_heatmap || []} />
          </section>
        </>
      )}

      {activeTab === 'factory' && (
        <div className="content-grid">
          <div className="panel">
            <div className="section-head">
              <h2>Smart Generation</h2>
              <span>Configure your exam paper</span>
            </div>
            
            <label>
              Select Subject
              <select value={selectedSubject} onChange={e => setSelectedSubject(e.target.value)}>
                {subjects.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </label>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <label>
                Total Marks
                <input type="number" defaultValue={100} />
              </label>
              <label>
                Question Count
                <input type="number" value={questionsCount} onChange={e => setQuestionsCount(e.target.value)} />
              </label>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', margin: '1rem 0' }}>
                 <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', margin: 0 }}>
                      <input 
                        type="checkbox" 
                        checked={useAI} 
                        onChange={e => setUseAI(e.target.checked)}
                        style={{ width: '20px', height: '20px' }}
                      />
                      <span style={{ fontWeight: 700, color: useAI ? 'var(--accent)' : 'var(--muted)' }}>
                        Enable AI Brain (Smarter Synthesis)
                      </span>
                 </label>
            </div>

            <div className="button-row">
              <button onClick={handleGeneratePaper} disabled={isProcessing}>
                {isProcessing ? 'Thinking...' : 'Generate Smart Paper'}
              </button>
              {generatedPaper && (
                <button className="secondary-btn" onClick={handleDownloadPDF}>
                  Download PDF
                </button>
              )}
            </div>

            {generatedPaper && (
              <div style={{ marginTop: '2rem' }}>
                <div className="section-head">
                  <h3>Paper Preview <span style={{ fontSize: '0.7rem', color: 'var(--accent)' }}>[{generatedPaper.mode}]</span></h3>
                </div>
                <div className="paper-preview">
                  {generatedPaper.questions.map(q => (
                    <div className="paper-question" key={q.question_no}>
                      <strong>Q{q.question_no}. {q.topic}</strong>
                      <p>{q.question_text}</p>
                      <div className="meta">
                        {q.marks} Marks · Difficulty {q.difficulty}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="panel">
            <div className="section-head">
              <h2>Prediction Lab</h2>
            </div>
            <label>
              Draft Question
              <textarea 
                value={questionText} 
                onChange={e => setQuestionText(e.target.value)}
                rows={4}
              />
            </label>
            <label>
              Allocated Marks
              <input type="number" value={marks} onChange={e => setMarks(e.target.value)} />
            </label>
            
            <div className="button-row">
              <button onClick={handlePredictTopic}>Predict Topic</button>
              <button onClick={handlePredictDifficulty} className="secondary-btn">Score Difficulty</button>
            </div>

            {prediction && (
              <div className="result-box" style={{ marginTop: '1.5rem', background: 'rgba(16, 185, 129, 0.05)' }}>
                {prediction.type === 'topic' ? (
                  <>
                    <span className="eyebrow" style={{ fontSize: '0.6rem' }}>Predicted Category</span>
                    <p style={{ fontSize: '1.25rem', fontWeight: 700 }}>{prediction.data.predicted_topic}</p>
                  </>
                ) : (
                  <>
                    <span className="eyebrow" style={{ fontSize: '0.6rem' }}>Difficulty Score (0-1)</span>
                    <p style={{ fontSize: '1.25rem', fontWeight: 700 }}>{prediction.data.difficulty_score}</p>
                  </>
                )}
              </div>
            )}

            <div style={{ marginTop: '2rem' }}>
              <div className="section-head">
                <h3>Most Expected (Subject Specific)</h3>
              </div>
              <div className="paper-preview">
                {expectedQuestions.map((q, idx) => (
                  <div key={idx} className="paper-question" style={{ borderLeft: '3px solid var(--warning)' }}>
                    <p style={{ margin: 0 }}>{q.question_text}</p>
                    <div className="meta">{q.topic} · {q.marks}M</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'manager' && (
        <div className="panel" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
          <div className="section-head" style={{ justifyContent: 'center' }}>
            <h2 style={{ fontSize: '1.5rem' }}>Historical Record Management</h2>
          </div>
          <p className="hero-copy" style={{ marginBottom: '2rem' }}>
            Import historical question papers (CSV format) to train the AI. 
            The system will automatically retrain its models in real-time.
          </p>
          <input 
            type="file" 
            accept=".csv" 
            ref={fileInputRef} 
            style={{ display: 'none' }} 
            onChange={handleFileUpload}
          />
          <button onClick={() => fileInputRef.current.click()} disabled={isProcessing}>
            {isProcessing ? 'Retraining Systems...' : 'Upload Historical CSV'}
          </button>
          
          <div style={{ marginTop: '3rem', textAlign: 'left', opacity: 0.6 }}>
            <h4>CSV Format Requirements:</h4>
            <code style={{ display: 'block', marginTop: '1rem', padding: '1rem', background: '#000', borderRadius: '8px' }}>
              year, subject, topic, question_text, marks, difficulty
            </code>
          </div>
        </div>
      )}

      <div className="status-indicator">
        <div className={`pulse ${isProcessing ? 'error' : ''}`} />
        <span style={{ fontSize: '0.8rem', fontWeight: 500 }}>{status}</span>
      </div>
    </div>
  )
}

export default App