/** Liste des documents de l'espace ; upload et suppression réservés aux éditeurs et admins. */
import { useCallback, useEffect, useState, type ChangeEvent } from 'react'
import { api, openDocument } from '../api'
import type { DocumentItem, Role } from '../types'

const STATUS: Record<DocumentItem['status'], { label: string; css: string }> = {
  pending: { label: 'En attente', css: 'bg-slate-100 text-slate-600' },
  processing: { label: 'Indexation...', css: 'bg-amber-100 text-amber-700' },
  ready: { label: 'Prêt', css: 'bg-green-100 text-green-700' },
  error: { label: 'Erreur', css: 'bg-red-100 text-red-700' },
}

export default function Documents({ workspaceId, role }: { workspaceId: number; role: Role }) {
  const [docs, setDocs] = useState<DocumentItem[]>([])
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)
  const canEdit = role === 'admin' || role === 'editor'

  const load = useCallback(
    () => api<DocumentItem[]>(`/api/workspaces/${workspaceId}/documents`).then(setDocs),
    [workspaceId],
  )

  useEffect(() => {
    load()
  }, [load])

  // Tant qu'un document est en cours d'indexation, on rafraîchit la liste toutes les 2 secondes
  useEffect(() => {
    if (!docs.some((d) => d.status === 'pending' || d.status === 'processing')) return
    const timer = setInterval(load, 2000)
    return () => clearInterval(timer)
  }, [docs, load])

  async function onUpload(e: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? [])
    e.target.value = ''
    setError('')
    setUploading(true)
    try {
      for (const file of files) {
        const form = new FormData()
        form.append('file', file)
        await api(`/api/workspaces/${workspaceId}/documents`, { method: 'POST', body: form })
      }
      await load()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setUploading(false)
    }
  }

  async function remove(doc: DocumentItem) {
    if (!confirm(`Supprimer "${doc.filename}" ?`)) return
    await api(`/api/documents/${doc.id}`, { method: 'DELETE' })
    load()
  }

  return (
    <div className="space-y-4">
      {canEdit ? (
        <label className="inline-block cursor-pointer rounded-md bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700">
          {uploading ? 'Envoi...' : '+ Ajouter des PDF'}
          <input type="file" accept="application/pdf" multiple hidden onChange={onUpload} disabled={uploading} />
        </label>
      ) : (
        <p className="text-sm text-slate-500">En tant que lecteur, vous pouvez consulter les documents et poser des questions.</p>
      )}
      {error && <p className="text-sm text-red-600">{error}</p>}

      <table className="w-full overflow-hidden rounded-xl border border-slate-200 bg-white text-sm">
        <thead className="bg-slate-50 text-left text-slate-500">
          <tr>
            <th className="px-4 py-2">Document</th>
            <th className="px-4 py-2">Pages</th>
            <th className="px-4 py-2">Statut</th>
            <th className="px-4 py-2" />
          </tr>
        </thead>
        <tbody>
          {docs.map((d) => (
            <tr key={d.id} className="border-t border-slate-100">
              <td className="px-4 py-2">
                <button onClick={() => openDocument(d.id)} className="text-indigo-700 hover:underline">
                  {d.filename}
                </button>
              </td>
              <td className="px-4 py-2">{d.pages || '-'}</td>
              <td className="px-4 py-2">
                <span title={d.error_message} className={`rounded-full px-2 py-0.5 text-xs ${STATUS[d.status].css}`}>
                  {STATUS[d.status].label}
                </span>
              </td>
              <td className="px-4 py-2 text-right">
                {canEdit && (
                  <button onClick={() => remove(d)} className="text-red-600 hover:underline">
                    Supprimer
                  </button>
                )}
              </td>
            </tr>
          ))}
          {docs.length === 0 && (
            <tr>
              <td colSpan={4} className="px-4 py-6 text-center text-slate-400">
                Aucun document
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
