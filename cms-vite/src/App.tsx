import { Outlet } from 'react-router-dom'
import { Toaster } from 'sonner'
import { WebSocketProvider } from '@/lib/websocket'

function App() {
  return (
    <WebSocketProvider debug={import.meta.env.DEV}>
      <Outlet />
      <Toaster position="top-right" richColors />
    </WebSocketProvider>
  )
}

export default App
