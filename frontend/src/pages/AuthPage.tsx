import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

export default function AuthPage({ mode }: { mode: 'login' | 'register' }) {
  const { user, login, register } = useAuth()
  const navigate = useNavigate()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/" replace />

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      if (mode === 'login') await login(email, password)
      else await register(fullName, email, password)
      navigate('/')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const input = 'w-full rounded-md border border-slate-300 px-3 py-2 focus:border-indigo-500 focus:outline-none'

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <form onSubmit={onSubmit} className="w-full max-w-sm space-y-4 rounded-xl bg-white p-8 shadow">
        <div>
          <h1 className="text-2xl font-bold text-indigo-700">DocuMind</h1>
          <p className="text-sm text-slate-500">
            {mode === 'login' ? 'Connexion à votre compte' : 'Créer un compte'}
          </p>
        </div>
        {mode === 'register' && (
          <input className={input} placeholder="Nom complet" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
        )}
        <input className={input} type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input
          className={input}
          type="password"
          placeholder="Mot de passe (8 caractères min.)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          minLength={8}
          required
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button disabled={busy} className="w-full rounded-md bg-indigo-600 py-2 font-medium text-white hover:bg-indigo-700 disabled:opacity-50">
          {mode === 'login' ? 'Se connecter' : "S'inscrire"}
        </button>
        <p className="text-center text-sm text-slate-500">
          {mode === 'login' ? (
            <>Pas de compte ? <Link className="text-indigo-600" to="/register">S'inscrire</Link></>
          ) : (
            <>Déjà inscrit ? <Link className="text-indigo-600" to="/login">Se connecter</Link></>
          )}
        </p>
      </form>
    </div>
  )
}
