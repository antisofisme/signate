import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { SidebarLayout } from './components/layout/SidebarLayout'
import Dashboard from './pages/Dashboard'
import DecisionMatrix from './pages/DecisionMatrix'
import DecisionList from './pages/DecisionList'
import DecisionDetail from './pages/DecisionDetail'
import Validator from './pages/Validator'
import Compare from './pages/Compare'
import SemanticSearch from './pages/SemanticSearch'
import DecisionWizard from './pages/DecisionWizard'
import ApprovalDashboard from './pages/ApprovalDashboard'
import RelationEditor from './pages/RelationEditor'
import DomainPage from './pages/DomainPage'
import EvolutionTimeline from './pages/EvolutionTimeline'
import ScopeProjection from './pages/ScopeProjection'
import RelationshipProjection from './pages/RelationshipProjection'
import ChangeSummary from './pages/ChangeSummary'
import TechStackProjection from './pages/TechStackProjection'
import AuditLog from './pages/AuditLog'
import ApiKeys from './pages/settings/ApiKeys'
import AISettings from './pages/settings/AISettings'
import MCPDashboard from './pages/MCPDashboard'
import Principles from './pages/Principles'
import Governance from './pages/Governance'
import AnalyticsDashboard from './pages/AnalyticsDashboard'
import DocumentGenerator from './pages/DocumentGenerator'
import RetrievalPlayground from './pages/RetrievalPlayground'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<SidebarLayout />}>
          <Route index element={<Dashboard />} />
          {/* Constitutional Foundation */}
          <Route path="principles" element={<Principles />} />
          <Route path="governance" element={<Governance />} />
          {/* Domain Routes */}
          <Route path="domain/:domainId" element={<DomainPage />} />
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
          <Route path="compare" element={<Compare />} />
          <Route path="search" element={<SemanticSearch />} />
          <Route path="audit" element={<AuditLog />} />
          {/* Workflow */}
          <Route path="wizard" element={<DecisionWizard />} />
          <Route path="approvals" element={<ApprovalDashboard />} />
          <Route path="relation-editor" element={<RelationEditor />} />
          {/* Settings */}
          <Route path="settings/api-keys" element={<ApiKeys />} />
          <Route path="settings/ai" element={<AISettings />} />
          <Route path="settings/mcp" element={<MCPDashboard />} />
          {/* New CORE Features */}
          <Route path="analytics" element={<AnalyticsDashboard />} />
          <Route path="docs" element={<DocumentGenerator />} />
          <Route path="retrieval" element={<RetrievalPlayground />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
