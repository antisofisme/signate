import { Outlet } from 'react-router-dom'
import { Toaster } from 'sonner'

function App() {
  return (
    <>
      <Outlet />
      <Toaster position="top-right" richColors />
    </>
  )
}

export default App
