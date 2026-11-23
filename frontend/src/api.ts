/**
 * Client HTTP de l'application.
 * - Ajoute automatiquement le token JWT ("Authorization: Bearer ...") à chaque requête.
 * - Si le access token a expiré (401), utilise le refresh token pour en obtenir un nouveau,
 *   puis rejoue la requête une fois.
 */
import type { Citation } from './types'

const API_URL = import.meta.env.VITE_API_URL ?? '' // vide en dev : le proxy Vite redirige /api

const ACCESS = 'documind_access'
const REFRESH = 'documind_refresh'

export const tokens = {
  get access() {
    return localStorage.getItem(ACCESS)
  },
  get refresh() {
    return localStorage.getItem(REFRESH)
  },
  save(access: string, refresh: string) {
    localStorage.setItem(ACCESS, access)
    localStorage.setItem(REFRESH, refresh)
  },
  clear() {
    localStorage.removeItem(ACCESS)
    localStorage.removeItem(REFRESH)
  },
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function tryRefresh(): Promise<boolean> {
  if (!tokens.refresh) return false
  const res = await fetch(`${API_URL}/api/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: tokens.refresh }),
  })
  if (!res.ok) {
    tokens.clear()
    return false
  }
  const data = await res.json()
  tokens.save(data.access_token, data.refresh_token)
  return true
}

/** fetch "brut" avec le token et le rafraîchissement automatique. */
export async function authFetch(path: string, init: RequestInit = {}, retry = true): Promise<Response> {
  const headers = new Headers(init.headers)
  if (tokens.access) headers.set('Authorization', `Bearer ${tokens.access}`)
  if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json')

  const res = await fetch(`${API_URL}${path}`, { ...init, headers })
  if (res.status === 401 && retry && (await tryRefresh())) {
    return authFetch(path, init, false)
  }
  if (!res.ok) {
    let message = `Erreur ${res.status}`
    try {
      const body = await res.json()
      message = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch {
      /* réponse sans JSON */
    }
    throw new ApiError(res.status, message)
  }
  return res
}

/** Requête JSON typée. */
export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await authFetch(path, init)
  return (res.status === 204 ? undefined : await res.json()) as T
}

/** Ouvre un PDF protégé à la bonne page (le navigateur gère "#page=N"). */
export async function openDocument(documentId: number, page = 1) {
  const res = await authFetch(`/api/documents/${documentId}/file`)
  const url = URL.createObjectURL(await res.blob())
  window.open(`${url}#page=${page}`, '_blank')
}

export type StreamEvent =
  | { type: 'meta'; conversation_id: number; citations: Citation[] }
  | { type: 'token'; text: string }
  | { type: 'error'; message: string }
  | { type: 'done' }

/**
 * Envoie une question et lit la réponse en streaming (Server-Sent Events).
 * Chaque événement arrive sous la forme "data: {...}\n\n" ; on appelle onEvent pour chacun.
 */
export async function streamChat(
  workspaceId: number,
  question: string,
  conversationId: number | null,
  onEvent: (e: StreamEvent) => void,
) {
  const res = await authFetch(`/api/workspaces/${workspaceId}/chat`, {
    method: 'POST',
    body: JSON.stringify({ question, conversation_id: conversationId }),
  })
  const reader = res.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const events = buffer.split('\n\n')
    buffer = events.pop() ?? '' // le dernier morceau peut être incomplet
    for (const raw of events) {
      const line = raw.trim()
      if (line.startsWith('data: ')) onEvent(JSON.parse(line.slice(6)))
    }
  }
}
