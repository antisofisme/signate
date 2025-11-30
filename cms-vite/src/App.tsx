import { Outlet } from 'react-router-dom'
import { Toaster } from 'sonner'
import { WebSocketProvider } from '@/lib/websocket'
import { UploadQueuePanel } from '@/features/uploads/components/UploadQueuePanel'

function App() {
  return (
    <WebSocketProvider debug={import.meta.env.DEV}>
      <Outlet />
      <Toaster position="top-right" richColors />
      <UploadQueuePanel />
    </WebSocketProvider>
  )
}

export default App
