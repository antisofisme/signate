import React from 'react'
import ReactDOM from 'react-dom/client'
import './styles/globals.css'

function TestApp() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-blue-600">CMS Vite is Working!</h1>
      <p className="mt-4">If you see this, React is rendering correctly.</p>
      <p className="mt-2">The issue might be with React Router or other components.</p>
      <div className="mt-8">
        <a href="/" className="text-blue-500 underline">Try Main App</a>
      </div>
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <TestApp />
  </React.StrictMode>,
)