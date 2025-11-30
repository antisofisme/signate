/**
 * App Component
 * Main application wrapper - minimal, just renders outlet
 * All global providers (Toaster, UploadQueue, WebSocket) are in main.tsx
 */

import { Outlet } from 'react-router-dom'

function App() {
  return <Outlet />
}

export default App
