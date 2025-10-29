# AuthContext Usage Guide

## Overview

AuthContext provides centralized authentication state management, eliminating prop drilling of `isAuthenticated` and `setIsAuthenticated` throughout the application.

## Location
`/mnt/g/khoirul/signate/web-admin/src/contexts/AuthContext.jsx`

## Benefits

- ✅ **No Prop Drilling** - Access auth state from any component
- ✅ **Centralized Auth Logic** - Login/logout in one place
- ✅ **Persistent Sessions** - Auto-restore from localStorage
- ✅ **User Profile Management** - Access user data globally
- ✅ **Auto-redirect** - Automatic redirect on logout
- ✅ **Token Validation** - Verify token on app initialization

## API Reference

### AuthProvider

Wrap your app with `AuthProvider` to make auth context available:

```javascript
import { AuthProvider } from './contexts/AuthContext'

function App() {
  return (
    <AuthProvider>
      {/* Your app */}
    </AuthProvider>
  )
}
```

### useAuth Hook

```javascript
const {
  isAuthenticated,  // boolean - Is user logged in?
  user,             // object - User profile data
  isLoading,        // boolean - Is auth state loading?
  login,            // function - Login user
  logout,           // function - Logout user
  updateUser,       // function - Update user profile
} = useAuth()
```

## Migration Guide

### Step 1: Update App.jsx

**Before:**
```javascript
function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    () => !!localStorage.getItem('token')
  )

  const PrivateRoute = ({ children }) => {
    return isAuthenticated ? children : <Navigate to="/login" />
  }

  return (
    <Router>
      <Routes>
        <Route path="/login" element={
          <Login setIsAuthenticated={setIsAuthenticated} />
        } />
        <Route path="/" element={
          <PrivateRoute>
            <Layout setIsAuthenticated={setIsAuthenticated}>
              <Dashboard />
            </Layout>
          </PrivateRoute>
        } />
      </Routes>
    </Router>
  )
}
```

**After:**
```javascript
import { AuthProvider } from './contexts/AuthContext'

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={
            <PrivateRoute>
              <Layout>
                <Dashboard />
              </Layout>
            </PrivateRoute>
          } />
        </Routes>
      </AuthProvider>
    </Router>
  )
}

// PrivateRoute component
function PrivateRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <div>Loading...</div>
  }

  return isAuthenticated ? children : <Navigate to="/login" />
}
```

### Step 2: Update Login.jsx

**Before:**
```javascript
export default function Login({ setIsAuthenticated }) {
  const handleLogin = async () => {
    const response = await authAPI.login(credentials)
    localStorage.setItem('token', response.data.token)
    setIsAuthenticated(true)
    navigate('/')
  }

  return <form onSubmit={handleLogin}>...</form>
}
```

**After:**
```javascript
import { useAuth } from '../contexts/AuthContext'

export default function Login() {
  const { login } = useAuth()

  const handleLogin = async () => {
    await login(credentials)
    navigate('/')
  }

  return <form onSubmit={handleLogin}>...</form>
}
```

### Step 3: Update Layout.jsx

**Before:**
```javascript
export default function Layout({ children, setIsAuthenticated }) {
  const handleLogout = () => {
    localStorage.removeItem('token')
    setIsAuthenticated(false)
    navigate('/login')
  }

  return (
    <div>
      <button onClick={handleLogout}>Logout</button>
      {children}
    </div>
  )
}
```

**After:**
```javascript
import { useAuth } from '../contexts/AuthContext'

export default function Layout({ children }) {
  const { logout, user } = useAuth()

  return (
    <div>
      <p>Welcome, {user?.username}</p>
      <button onClick={logout}>Logout</button>
      {children}
    </div>
  )
}
```

### Step 4: Use in Any Component

Now you can access auth state from any component without prop drilling:

```javascript
import { useAuth } from '../contexts/AuthContext'

function MyComponent() {
  const { isAuthenticated, user, logout } = useAuth()

  if (!isAuthenticated) {
    return <div>Please login</div>
  }

  return (
    <div>
      <h1>Hello {user?.username}!</h1>
      <p>Email: {user?.email}</p>
      <button onClick={logout}>Logout</button>
    </div>
  )
}
```

## Advanced Usage

### Protected Components

```javascript
function AdminPanel() {
  const { user } = useAuth()

  if (user?.role !== 'admin') {
    return <Navigate to="/" />
  }

  return <div>Admin Panel</div>
}
```

### Conditional Rendering

```javascript
function Navbar() {
  const { isAuthenticated, user } = useAuth()

  return (
    <nav>
      {isAuthenticated ? (
        <>
          <span>Welcome, {user?.username}</span>
          <LogoutButton />
        </>
      ) : (
        <Link to="/login">Login</Link>
      )}
    </nav>
  )
}
```

### Loading States

```javascript
function App() {
  const { isLoading } = useAuth()

  if (isLoading) {
    return <LoadingScreen />
  }

  return <Routes>...</Routes>
}
```

## Important Notes

1. **AuthProvider must be inside Router** - Because it uses `useNavigate()`
2. **Token validation on mount** - App checks token validity on load
3. **Automatic logout on 401** - API interceptor already handles this
4. **Backward compatible** - `setIsAuthenticated` still available during migration

## Testing

```javascript
import { render } from '@testing-library/react'
import { AuthProvider } from './contexts/AuthContext'
import { BrowserRouter } from 'react-router-dom'

function renderWithAuth(component) {
  return render(
    <BrowserRouter>
      <AuthProvider>
        {component}
      </AuthProvider>
    </BrowserRouter>
  )
}

test('shows user info', () => {
  const { getByText } = renderWithAuth(<MyComponent />)
  expect(getByText(/Welcome/)).toBeInTheDocument()
})
```

## Migration Checklist

- [ ] Import `AuthProvider` in App.jsx
- [ ] Wrap `<Router>` children with `<AuthProvider>`
- [ ] Remove `isAuthenticated` state from App.jsx
- [ ] Remove `setIsAuthenticated` prop from Login component
- [ ] Update Login.jsx to use `useAuth()` hook
- [ ] Remove `setIsAuthenticated` prop from Layout component
- [ ] Update Layout.jsx to use `useAuth()` hook
- [ ] Update PrivateRoute to use `useAuth()` hook
- [ ] Test login flow
- [ ] Test logout flow
- [ ] Test page refresh (persistent session)
- [ ] Test protected routes
