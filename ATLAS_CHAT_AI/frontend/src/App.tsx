import { Routes, Route } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'
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
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/search" element={<Search />} />
        <Route path="/memory" element={<Memory />} />
        <Route path="/sessions" element={<Sessions />} />
        <Route path="/tenants" element={<Tenants />} />
        <Route path="/users" element={<Users />} />
        <Route path="/api-keys" element={<APIKeys />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}

export default App
