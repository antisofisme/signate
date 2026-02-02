/**
 * ATLAS_SEMAR Frontend - Root Component
 * Follows PANDAWA Clean Architecture standards
 */
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import AssistantControl from '@features/assistant/components/AssistantControl'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto py-6 px-4">
            <h1 className="text-3xl font-bold text-gray-900">
              ATLAS SEMAR - Voice Assistant
            </h1>
          </div>
        </header>

        <main className="max-w-7xl mx-auto py-6 px-4">
          <Routes>
            <Route path="/" element={<AssistantControl />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
