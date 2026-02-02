/**
 * Invitation Accept Page
 * Public page for accepting tenant invitations
 */

import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useToast } from '@/hooks/use-toast'
import { useAcceptInvitation } from '@/domains/tenant/api'
import { useAuthStore } from '@/stores/authStore'
import { Building2, CheckCircle, XCircle, Loader2, LogIn } from 'lucide-react'

export function InvitationAccept() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { toast } = useToast()
  const token = searchParams.get('token')
  const { isAuthenticated } = useAuthStore()
  const acceptInvitation = useAcceptInvitation()

  const [status, setStatus] = useState<'pending' | 'accepting' | 'success' | 'error'>('pending')
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    // Auto-accept if user is authenticated and has token
    if (isAuthenticated && token && status === 'pending') {
      handleAccept()
    }
  }, [isAuthenticated, token])

  const handleAccept = async () => {
    if (!token) {
      setStatus('error')
      setErrorMessage('Invalid invitation link. Please check your email for the correct link.')
      return
    }

    setStatus('accepting')
    try {
      const result = await acceptInvitation.mutateAsync({ token })
      setStatus('success')
      toast({
        title: 'Invitation accepted',
        description: 'You have joined the tenant successfully.',
      })
      // Redirect to the tenant after a short delay
      setTimeout(() => {
        navigate(`/app/tenant/${result.data?.tenantId || ''}`)
      }, 2000)
    } catch (err) {
      setStatus('error')
      setErrorMessage(
        err instanceof Error
          ? err.message
          : 'Failed to accept invitation. The link may have expired.'
      )
    }
  }

  // No token provided
  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 p-4">
        <Card className="max-w-md w-full">
          <CardHeader className="text-center">
            <XCircle className="h-12 w-12 mx-auto text-destructive mb-4" />
            <CardTitle>Invalid Invitation</CardTitle>
            <CardDescription>
              The invitation link is invalid or missing. Please check your email for the correct link.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <Button asChild>
              <Link to="/">Go to Home</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  // User not authenticated
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 p-4">
        <Card className="max-w-md w-full">
          <CardHeader className="text-center">
            <Building2 className="h-12 w-12 mx-auto text-primary mb-4" />
            <CardTitle>Accept Invitation</CardTitle>
            <CardDescription>
              You've been invited to join a team. Please sign in or create an account to accept.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button className="w-full" asChild>
              <Link to={`/login?redirect=${encodeURIComponent(window.location.href)}`}>
                <LogIn className="h-4 w-4 mr-2" />
                Sign In to Accept
              </Link>
            </Button>
            <div className="text-center text-sm text-muted-foreground">
              Don't have an account?{' '}
              <Link
                to={`/register?redirect=${encodeURIComponent(window.location.href)}`}
                className="text-primary hover:underline"
              >
                Create one
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Processing states
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 p-4">
      <Card className="max-w-md w-full">
        <CardHeader className="text-center">
          {status === 'accepting' && (
            <>
              <Loader2 className="h-12 w-12 mx-auto text-primary mb-4 animate-spin" />
              <CardTitle>Accepting Invitation</CardTitle>
              <CardDescription>Please wait while we process your invitation...</CardDescription>
            </>
          )}
          {status === 'success' && (
            <>
              <CheckCircle className="h-12 w-12 mx-auto text-green-600 mb-4" />
              <CardTitle>Welcome to the Team!</CardTitle>
              <CardDescription>
                You've successfully joined the tenant. Redirecting to dashboard...
              </CardDescription>
            </>
          )}
          {status === 'error' && (
            <>
              <XCircle className="h-12 w-12 mx-auto text-destructive mb-4" />
              <CardTitle>Invitation Failed</CardTitle>
              <CardDescription>{errorMessage}</CardDescription>
            </>
          )}
          {status === 'pending' && (
            <>
              <Building2 className="h-12 w-12 mx-auto text-primary mb-4" />
              <CardTitle>Accept Invitation</CardTitle>
              <CardDescription>
                Click the button below to join the team.
              </CardDescription>
            </>
          )}
        </CardHeader>
        <CardContent className="text-center">
          {status === 'pending' && (
            <Button onClick={handleAccept}>
              Accept Invitation
            </Button>
          )}
          {status === 'error' && (
            <div className="space-y-2">
              <Button variant="outline" onClick={() => navigate('/')}>
                Go to Home
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
