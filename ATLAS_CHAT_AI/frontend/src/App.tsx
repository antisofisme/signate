/**
 * ATLAS_CHAT_AI - Main Application
 * RAG Chat with 4-Layer Memory System
 *
 * Architecture: MANTRA/PUGUH style with domain-based navigation
 */

import { Routes, Route } from 'react-router-dom'
import { SidebarLayout } from '@/components/layout/SidebarLayout'
import {
  Dashboard,
  Chat,
  Search,
  Memory,
  Sessions,
  Tenants,
  Users,
  APIKeys,
  Settings,
} from '@/pages'

function App() {
  return (
    <Routes>
      <Route path="/" element={<SidebarLayout />}>
        {/* Overview */}
        <Route index element={<Dashboard />} />

        {/* Chat & AI Domain */}
        <Route path="chat" element={<Chat />} />
        <Route path="search" element={<Search />} />
        <Route path="memory" element={<Memory />} />
        <Route path="sessions" element={<Sessions />} />

        {/* Administration Domain */}
        <Route path="tenants" element={<Tenants />} />
        <Route path="users" element={<Users />} />
        <Route path="api-keys" element={<APIKeys />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}

export default App
