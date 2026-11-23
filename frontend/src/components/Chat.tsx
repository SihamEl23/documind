/**
 * Zone de chat : historique des conversations à gauche, messages à droite.
 * La réponse s'affiche mot par mot pendant que le LLM l'écrit (streaming).
 * Les citations [1], [2]... sont cliquables et ouvrent le PDF à la bonne page.
 */
import { useEffect, useRef, useState, type FormEvent } from 'react'
import { api, openDocument, streamChat } from '../api'
import type { ChatMessage, Citation, Conversation } from '../types'

export default function Chat({ workspaceId }: { workspaceId: number }) {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [conversationId, setConversationId] = useState<number | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [question, setQuestion] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [error, setError] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  const loadConversations = () =>
    api<Conversation[]>(`/api/workspaces/${workspaceId}/conversations`).then(setConversations)

  useEffect(() => {
    loadConversations()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspaceId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function openConversation(id: number) {
    setConversationId(id)
    setMessages(await api<ChatMessage[]>(`/api/conversations/${id}/messages`))
  }

  function newConversation() {
    setConversationId(null)
    setMessages([])
  }

  /** Met à jour le dernier message (celui de l'assistant en cours d'écriture). */
  function updateLast(update: (m: ChatMessage) => ChatMessage) {
    setMessages((list) => [...list.slice(0, -1), update(list[list.length - 1])])
  }

  async function ask(e: FormEvent) {
    e.preventDefault()
    const q = question.trim()
    if (!q || streaming) return
    setQuestion('')
    setError('')
    setStreaming(true)
    setMessages((list) => [
      ...list,
      { role: 'user', content: q, citations: [] },
      { role: 'assistant', content: '', citations: [] },
    ])
    try {
      await streamChat(workspaceId, q, conversationId, (event) => {
        if (event.type === 'meta') {
          setConversationId(event.conversation_id)
          updateLast((m) => ({ ...m, citations: event.citations }))
        } else if (event.type === 'token') {
          updateLast((m) => ({ ...m, content: m.content + event.text }))
        } else if (event.type === 'error') {
          setError(event.message)
        }
      })
      loadConversations()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setStreaming(false)
    }
  }

  return (
    <div className="grid gap-4 md:grid-cols-[220px_1fr]">
      <aside className="space-y-2">
        <button onClick={newConversation} className="w-full rounded-md bg-indigo-600 px-3 py-2 text-sm text-white hover:bg-indigo-700">
          + Nouvelle question
        </button>
        <ul className="space-y-1 text-sm">
          {conversations.map((c) => (
            <li key={c.id}>
              <button
                onClick={() => openConversation(c.id)}
                className={`w-full truncate rounded px-2 py-1 text-left hover:bg-slate-100 ${c.id === conversationId ? 'bg-slate-200' : ''}`}
              >
                {c.title}
              </button>
            </li>
          ))}
        </ul>
      </aside>

      <section className="flex h-[70vh] flex-col rounded-xl border border-slate-200 bg-white">
        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          {messages.length === 0 && (
            <p className="text-center text-slate-400">Posez une question sur les documents de cet espace.</p>
          )}
          {messages.map((m, i) => (
            <MessageBubble key={i} message={m} typing={streaming && i === messages.length - 1} />
          ))}
          <div ref={bottomRef} />
        </div>
        {error && <p className="px-4 text-sm text-red-600">{error}</p>}
        <form onSubmit={ask} className="flex gap-2 border-t border-slate-200 p-3">
          <input
            className="flex-1 rounded-md border border-slate-300 px-3 py-2"
            placeholder="Ex. : Combien de jours de congé par an ?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={streaming}
          />
          <button disabled={streaming} className="rounded-md bg-indigo-600 px-4 text-white disabled:opacity-50">
            Envoyer
          </button>
        </form>
      </section>
    </div>
  )
}

function MessageBubble({ message, typing }: { message: ChatMessage; typing: boolean }) {
  const isUser = message.role === 'user'
  return (
    <div className={isUser ? 'flex justify-end' : ''}>
      <div className={`max-w-[85%] rounded-lg px-4 py-2 ${isUser ? 'bg-indigo-600 text-white' : 'bg-slate-100'}`}>
        <p className="whitespace-pre-wrap" dir="auto">
          {message.content}
          {typing && <span className="animate-pulse">▍</span>}
        </p>
        {!isUser && message.citations.length > 0 && <Sources citations={message.citations} />}
      </div>
    </div>
  )
}

function Sources({ citations }: { citations: Citation[] }) {
  return (
    <div className="mt-2 border-t border-slate-200 pt-2">
      <p className="mb-1 text-xs font-medium text-slate-500">Sources</p>
      <div className="flex flex-wrap gap-1">
        {citations.map((c) => (
          <button
            key={c.index}
            title={c.excerpt}
            onClick={() => openDocument(c.document_id, c.page)}
            className="rounded border border-slate-300 bg-white px-2 py-0.5 text-xs hover:border-indigo-500"
          >
            [{c.index}] {c.filename}, p. {c.page}
          </button>
        ))}
      </div>
    </div>
  )
}
