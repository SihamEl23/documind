import { StrictMode, type ReactNode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth'
import Layout from './components/Layout'
import './index.css'
import AuthPage from './pages/AuthPage'
import WorkspacePage from './pages/WorkspacePage'
import WorkspacesPage from './pages/WorkspacesPage'

/** Redirige vers /login si personne n'est connecté. */
function Protected({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <p className="p-8 text-slate-500">Chargement...</p>
  return user ? <Layout>{children}</Layout> : <Navigate to="/login" replace />
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<AuthPage mode="login" />} />
          <Route path="/register" element={<AuthPage mode="register" />} />
          <Route path="/" element={<Protected><WorkspacesPage /></Protected>} />
          <Route path="/workspaces/:id" element={<Protected><WorkspacePage /></Protected>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  </StrictMode>,
)
