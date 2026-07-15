const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

const url = path => `${API_BASE}/api/v1${path}`

async function unwrap(res) {
  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      const body = await res.json()
      // FastAPI returns {"detail": "..."} or {"detail": [{...}]} for 422
      if (typeof body.detail === 'string') detail = body.detail
      else if (Array.isArray(body.detail)) detail = body.detail[0]?.msg ?? detail
    } catch {
      /* non-JSON error body (e.g. proxy 502) — keep the status message */
    }
    throw new Error(detail)
  }
  return res.json()
}

export async function uploadDocument(file, { signal } = {}) {
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch(url('/upload'), { method: 'POST', body: formData, signal })
  return unwrap(res)
}

export async function queryDocuments(query, { topK = 5, signal } = {}) {
  const res = await fetch(url('/query'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, top_k: topK }),
    signal,
  })
  return unwrap(res)
}