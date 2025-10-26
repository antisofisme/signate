import { createContext, useContext, useState, useEffect } from 'react'

const ThemeContext = createContext()

export const useTheme = () => {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider')
  }
  return context
}

export const ThemeProvider = ({ children }) => {
  // Simple initial state - always start with light
  const [theme, setTheme] = useState('light')

  // On mount, check localStorage and apply saved theme
  useEffect(() => {
    const saved = localStorage.getItem('theme')
    if (saved === 'dark') {
      setTheme('dark')
    }
  }, [])

  // Apply theme to DOM whenever it changes
  useEffect(() => {
    const html = document.documentElement

    if (theme === 'dark') {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }

    // Save to localStorage
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light'
    setTheme(newTheme)
  }

  const value = {
    theme,
    setTheme,
    toggleTheme,
    isDark: theme === 'dark'
  }

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  )
}
