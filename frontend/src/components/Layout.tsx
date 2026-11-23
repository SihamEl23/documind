import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth'

export default function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth()
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
          <Link to="/" className="text-xl font-bold text-indigo-700">
            DocuMind
          </Link>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-slate-600">{user?.full_name}</span>
            <button onClick={logout} className="rounded-md border border-slate-300 px-3 py-1 hover:bg-slate-100">
              Déconnexion
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-6">{children}</main>
    </div>
  )
}
