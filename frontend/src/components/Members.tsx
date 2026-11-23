/** Membres de l'espace. Seul un administrateur peut inviter, changer un rôle ou retirer un membre. */
import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { api } from '../api'
import { ROLE_LABELS, type Member, type Role } from '../types'

const ROLES: Role[] = ['viewer', 'editor', 'admin']

export default function Members({ workspaceId, role }: { workspaceId: number; role: Role }) {
  const [members, setMembers] = useState<Member[]>([])
  const [email, setEmail] = useState('')
  const [newRole, setNewRole] = useState<Role>('viewer')
  const [error, setError] = useState('')
  const isAdmin = role === 'admin'

  const load = useCallback(
    () => api<Member[]>(`/api/workspaces/${workspaceId}/members`).then(setMembers),
    [workspaceId],
  )

  useEffect(() => {
    load()
  }, [load])

  async function run(action: () => Promise<unknown>) {
    setError('')
    try {
      await action()
      await load()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  function invite(e: FormEvent) {
    e.preventDefault()
    run(async () => {
      await api(`/api/workspaces/${workspaceId}/members`, {
        method: 'POST',
        body: JSON.stringify({ email, role: newRole }),
      })
      setEmail('')
    })
  }

  return (
    <div className="space-y-4">
      {isAdmin && (
        <form onSubmit={invite} className="flex flex-wrap gap-2">
          <input
            type="email"
            className="flex-1 rounded-md border border-slate-300 px-3 py-2"
            placeholder="Email d'un utilisateur inscrit"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <select className="rounded-md border border-slate-300 px-3" value={newRole} onChange={(e) => setNewRole(e.target.value as Role)}>
            {ROLES.map((r) => (
              <option key={r} value={r}>{ROLE_LABELS[r]}</option>
            ))}
          </select>
          <button className="rounded-md bg-indigo-600 px-4 text-white">Ajouter</button>
        </form>
      )}
      {error && <p className="text-sm text-red-600">{error}</p>}

      <ul className="divide-y divide-slate-100 rounded-xl border border-slate-200 bg-white">
        {members.map((m) => (
          <li key={m.user_id} className="flex items-center justify-between px-4 py-3">
            <div>
              <p className="font-medium">{m.full_name}</p>
              <p className="text-sm text-slate-500">{m.email}</p>
            </div>
            {isAdmin ? (
              <div className="flex items-center gap-2">
                <select
                  className="rounded-md border border-slate-300 px-2 py-1 text-sm"
                  value={m.role}
                  onChange={(e) =>
                    run(() =>
                      api(`/api/workspaces/${workspaceId}/members/${m.user_id}`, {
                        method: 'PATCH',
                        body: JSON.stringify({ role: e.target.value }),
                      }),
                    )
                  }
                >
                  {ROLES.map((r) => (
                    <option key={r} value={r}>{ROLE_LABELS[r]}</option>
                  ))}
                </select>
                <button
                  onClick={() => run(() => api(`/api/workspaces/${workspaceId}/members/${m.user_id}`, { method: 'DELETE' }))}
                  className="text-sm text-red-600 hover:underline"
                >
                  Retirer
                </button>
              </div>
            ) : (
              <span className="text-sm text-slate-500">{ROLE_LABELS[m.role]}</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
