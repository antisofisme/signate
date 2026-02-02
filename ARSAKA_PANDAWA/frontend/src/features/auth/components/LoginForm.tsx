/**
 * ARSAKA_PANDAWA Frontend - Login Form Component
 * User authentication form
 */

import { useState } from 'react'
import { useLogin } from '../hooks/useAuth'
import { AuthFormData } from '../types'
import Button from '@shared/components/ui/Button'

export default function LoginForm() {
  const [formData, setFormData] = useState<AuthFormData>({
    username: '',
    password: '',
    tenant_slug: '',
  })

  const loginMutation = useLogin()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    loginMutation.mutate(formData)
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }))
  }

  return (
    <div className="login-form">
      <h2>Login to ARSAKA_PANDAWA</h2>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="username">Username or Email</label>
          <input
            type="text"
            id="username"
            name="username"
            value={formData.username}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="tenant_slug">Tenant (Optional)</label>
          <input
            type="text"
            id="tenant_slug"
            name="tenant_slug"
            value={formData.tenant_slug}
            onChange={handleChange}
            placeholder="Leave empty for personal account"
          />
        </div>

        {loginMutation.isError && (
          <div className="error-message">
            Login failed. Please check your credentials.
          </div>
        )}

        <Button type="submit" disabled={loginMutation.isPending}>
          {loginMutation.isPending ? 'Logging in...' : 'Login'}
        </Button>
      </form>
    </div>
  )
}
