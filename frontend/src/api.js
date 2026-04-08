const API_BASE = 'http://localhost:8000'

async function request(path, options = {}) {
  const isFormData = options.body instanceof FormData
  const headers = { ...options.headers }
  
  if (!isFormData) {
    headers['Content-Type'] = 'application/json'
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const body = await response.text()
    throw new Error(body || `Request failed with ${response.status}`)
  }

  if (response.headers.get('Content-Type') === 'application/pdf') {
    return response.blob()
  }

  return response.json()
}

export const api = {
  health: () => request('/health'),
  analytics: () => request('/analytics/topic-frequency'),
  subjects: () => request('/metadata/subjects'),
  uploadCSV: (formData) => request('/upload/csv', {
    method: 'POST',
    body: formData,
  }),
  predictTopic: (question_text) => request('/predict/topic', {
    method: 'POST',
    body: JSON.stringify({ question_text }),
  }),
  predictDifficulty: (question_text, marks) => request('/predict/difficulty', {
    method: 'POST',
    body: JSON.stringify({ question_text, marks }),
  }),
  expectedQuestions: (subject, limit = 8) => request(`/questions/expected?subject=${encodeURIComponent(subject)}&limit=${limit}`),
  generatePaper: (payload) => request('/papers/generate', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  downloadPaper: (payload) => request('/papers/download', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  exportPowerBI: () => request('/export/powerbi'),
}