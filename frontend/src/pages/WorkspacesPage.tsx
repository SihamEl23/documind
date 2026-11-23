import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { ROLE_LABELS, type Workspace } from '../types'

export default function WorkspacesPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    api<Workspace[]>('/api/workspaces').then(setWorkspaces).catch((e) => setError(e.message))
  }, [])

  async function create(e: FormEvent) {
    e.preventDefault()
    try {
      const ws = await api<Workspace>('/api/workspaces', {
        method: 'POST',
        body: JSON.stringify({ name, description }),
      })
      setWorkspaces((list) => [...list, ws])
      setName('')
      setDescription('')
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Mes espaces</h1>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {workspaces.map((ws) => (
          <Link key={ws.id} to={`/workspaces/${ws.id}`} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm hover:border-indigo-400">
            <div className="flex items-start justify-between">
              <h2 className="text-lg font-medium">{ws.name}</h2>
              <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-xs text-indigo-700">{ROLE_LABELS[ws.my_role]}</span>
            </div>
            <p className="mt-1 text-sm text-slate-500">{ws.description || 'Aucune description'}</p>
          </Link>
        ))}
        {workspaces.length === 0 && <p className="text-slate-500">Vous n'êtes membre d'aucun espace pour l'instant.</p>}
      </div>

      <form onSubmit={create} className="max-w-xl space-y-3 rounded-xl border border-slate-200 bg-white p-5">
        <h2 className="font-medium">Créer un espace</h2>
        <input className="w-full rounded-md border border-slate-300 px-3 py-2" placeholder="Nom (ex. Ressources humaines)" value={name} onChange={(e) => setName(e.target.value)} required minLength={2} />
        <input className="w-full rounded-md border border-slate-300 px-3 py-2" placeholder="Description (optionnel)" value={description} onChange={(e) => setDescription(e.target.value)} />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button className="rounded-md bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-700">Créer</button>
      </form>
    </div>
  )
}
