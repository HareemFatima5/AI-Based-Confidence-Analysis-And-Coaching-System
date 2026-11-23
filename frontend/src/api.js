export async function api(path, body) {
  const post = body !== undefined
  const r = await fetch('/api/' + path, {
    method: post ? 'POST' : 'GET',
    credentials: 'same-origin',
    headers: post ? { 'Content-Type': 'application/json' } : {},
    body: post ? JSON.stringify(body) : undefined,
  })
  const d = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(typeof d.detail === 'string' ? d.detail : 'Please check your details and try again.')
  return d
}
