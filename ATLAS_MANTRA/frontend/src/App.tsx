import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { SidebarLayout } from './components/layout/SidebarLayout'
import Dashboard from './pages/Dashboard'
import DecisionMatrix from './pages/DecisionMatrix'
import DecisionList from './pages/DecisionList'
import DecisionDetail from './pages/DecisionDetail'
import Validator from './pages/Validator'
import GroupPage from './pages/GroupPage'
import EvolutionTimeline from './pages/EvolutionTimeline'
import ScopeProjection from './pages/ScopeProjection'
import RelationshipProjection from './pages/RelationshipProjection'
import ChangeSummary from './pages/ChangeSummary'
import TechStackProjection from './pages/TechStackProjection'
import AuditLog from './pages/AuditLog'
import ApiKeys from './pages/settings/ApiKeys'
import AISettings from './pages/settings/AISettings'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<SidebarLayout />}>
          <Route index element={<Dashboard />} />
          {/* Group Routes */}
          <Route path="group/:groupNum" element={<GroupPage />} />
          {/* Global Views */}
          <Route path="matrix" element={<DecisionMatrix />} />
          <Route path="decisions" element={<DecisionList />} />
          <Route path="decisions/:id" element={<DecisionDetail />} />
          {/* Projection Views per MANTRA-L1-PROJECTION-CATALOG-001 */}
          <Route path="timeline" element={<EvolutionTimeline />} />
          <Route path="scope" element={<ScopeProjection />} />
          <Route path="relationships" element={<RelationshipProjection />} />
          <Route path="changes" element={<ChangeSummary />} />
          <Route path="tech-stack" element={<TechStackProjection />} />
          {/* Tools */}
          <Route path="validate" element={<Validator />} />
          <Route path="audit" element={<AuditLog />} />
          {/* Settings */}
          <Route path="settings/api-keys" element={<ApiKeys />} />
          <Route path="settings/ai" element={<AISettings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
