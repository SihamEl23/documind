import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api'
import Chat from '../components/Chat'
import Documents from '../components/Documents'
import Members from '../components/Members'
import { ROLE_LABELS, type Workspace } from '../types'

type Tab = 'chat' | 'documents' | 'members'

export default function WorkspacePage() {
  const id = Number(useParams().id)
  const [ws, setWs] = useState<Workspace | null>(null)
  const [tab, setTab] = useState<Tab>('chat')
  const [error, setError] = useState('')

  useEffect(() => {
    api<Workspace>(`/api/workspaces/${id}`).then(setWs).catch((e) => setError(e.message))
  }, [id])

  if (error) return <p className="text-red-600">{error}</p>
  if (!ws) return <p className="text-slate-500">Chargement...</p>

  const tabs: [Tab, string][] = [
    ['chat', 'Questions'],
    ['documents', 'Documents'],
    ['members', 'Membres'],
  ]

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-semibold">{ws.name}</h1>
        <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-xs text-indigo-700">{ROLE_LABELS[ws.my_role]}</span>
      </div>
      <nav className="flex gap-2 border-b border-slate-200">
        {tabs.map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`-mb-px border-b-2 px-4 py-2 text-sm ${tab === key ? 'border-indigo-600 font-medium text-indigo-700' : 'border-transparent text-slate-500'}`}
          >
            {label}
          </button>
        ))}
      </nav>
      {tab === 'chat' && <Chat workspaceId={id} />}
      {tab === 'documents' && <Documents workspaceId={id} role={ws.my_role} />}
      {tab === 'members' && <Members workspaceId={id} role={ws.my_role} />}
    </div>
  )
}
