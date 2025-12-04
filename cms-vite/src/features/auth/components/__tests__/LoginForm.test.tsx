/**
 * LoginForm Component Tests
 * Tests for login form with validation
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@/test/utils'
import userEvent from '@testing-library/user-event'
import { LoginForm } from '../LoginForm'

// Mock useLogin hook - use factory function
const mockLogin = vi.fn()
vi.mock('../../hooks/useAuth', () => ({
  useLogin: () => ({
    mutate: mockLogin,
    isPending: false,
  }),
}))

// Mock i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue?: string) => defaultValue || key,
  }),
}))

describe('LoginForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders login form with all fields', () => {
    render(<LoginForm />)

    expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument()
  })

  it('does not call login when form is empty', async () => {
    const user = userEvent.setup()
    render(<LoginForm />)

    // Click submit without filling any fields
    const submitButton = screen.getByRole('button', { name: /login/i })
    await user.click(submitButton)

    // Login should NOT be called with invalid form
    expect(mockLogin).not.toHaveBeenCalled()
  })

  it('does not call login with invalid username', async () => {
    const user = userEvent.setup()
    render(<LoginForm />)

    const usernameInput = screen.getByLabelText(/username/i)
    const passwordInput = screen.getByLabelText(/password/i)

    await user.type(usernameInput, 'ab') // Too short
    await user.type(passwordInput, 'validpassword')

    const submitButton = screen.getByRole('button', { name: /login/i })
    await user.click(submitButton)

    // Login should NOT be called with invalid username
    expect(mockLogin).not.toHaveBeenCalled()
  })

  it('shows validation error for short password', async () => {
    const user = userEvent.setup()
    render(<LoginForm />)

    const usernameInput = screen.getByLabelText(/username/i)
    const passwordInput = screen.getByLabelText(/password/i)

    await user.type(usernameInput, 'testuser')
    await user.type(passwordInput, 'ab')

    const submitButton = screen.getByRole('button', { name: /login/i })
    await user.click(submitButton)

    await waitFor(
      () => {
        expect(screen.getByText(/password minimal 3 karakter/i)).toBeInTheDocument()
      },
      { timeout: 2000 }
    )
  })

  it('calls login function with valid credentials', async () => {
    const user = userEvent.setup()
    render(<LoginForm />)

    const usernameInput = screen.getByLabelText(/username/i)
    const passwordInput = screen.getByLabelText(/password/i)

    await user.type(usernameInput, 'testuser')
    await user.type(passwordInput, 'password123')

    const submitButton = screen.getByRole('button', { name: /login/i })
    await user.click(submitButton)

    await waitFor(
      () => {
        expect(mockLogin).toHaveBeenCalledWith({
          username: 'testuser',
          password: 'password123',
        })
      },
      { timeout: 2000 }
    )
  })

  it('has accessible form with aria-label', () => {
    render(<LoginForm />)
    expect(screen.getByRole('form', { name: /login form/i })).toBeInTheDocument()
  })
})
