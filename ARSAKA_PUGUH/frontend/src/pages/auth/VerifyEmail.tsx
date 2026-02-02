/**
 * ARSAKA_PUGUH - Verify Email Page
 */

import { useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Scale, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { useVerifyEmail } from '@/features/auth/hooks'

export function VerifyEmail() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const verifyEmailMutation = useVerifyEmail()

  useEffect(() => {
    if (token && !verifyEmailMutation.isSuccess && !verifyEmailMutation.isError) {
      verifyEmailMutation.mutate(token)
    }
  }, [token])

  const getErrorMessage = () => {
    const error = verifyEmailMutation.error as any
    if (error?.response?.data?.error) {
      return error.response.data.error.message
    }
    return 'This verification link is invalid or has expired.'
  }

  // No token provided
  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <Link to="/" className="inline-flex items-center gap-2">
              <Scale className="h-10 w-10 text-amber-500" />
              <span className="font-bold text-2xl">ATLAS PUGUH</span>
            </Link>
          </div>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
                  <AlertCircle className="h-8 w-8 text-red-600" />
                </div>
                <h2 className="text-xl font-semibold mb-2">Invalid Verification Link</h2>
                <p className="text-muted-foreground mb-6">
                  No verification token was provided. Please check your email for the correct link.
                </p>
                <div className="space-y-3">
                  <Link to="/register">
                    <Button className="w-full">Register New Account</Button>
                  </Link>
                  <Link to="/login">
                    <Button variant="outline" className="w-full">
                      Back to Login
                    </Button>
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  // Loading state
  if (verifyEmailMutation.isPending) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <Link to="/" className="inline-flex items-center gap-2">
              <Scale className="h-10 w-10 text-amber-500" />
              <span className="font-bold text-2xl">ATLAS PUGUH</span>
            </Link>
          </div>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <Loader2 className="h-12 w-12 text-amber-500 animate-spin mx-auto mb-4" />
                <h2 className="text-xl font-semibold mb-2">Verifying your email...</h2>
                <p className="text-muted-foreground">
                  Please wait while we verify your email address.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  // Error state
  if (verifyEmailMutation.isError) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <Link to="/" className="inline-flex items-center gap-2">
              <Scale className="h-10 w-10 text-amber-500" />
              <span className="font-bold text-2xl">ATLAS PUGUH</span>
            </Link>
          </div>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
                  <AlertCircle className="h-8 w-8 text-red-600" />
                </div>
                <h2 className="text-xl font-semibold mb-2">Verification Failed</h2>
                <p className="text-muted-foreground mb-6">{getErrorMessage()}</p>
                <div className="space-y-3">
                  <Link to="/register">
                    <Button className="w-full">Register New Account</Button>
                  </Link>
                  <Link to="/login">
                    <Button variant="outline" className="w-full">
                      Back to Login
                    </Button>
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  // Success state (will redirect, but show this briefly)
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2">
            <Scale className="h-10 w-10 text-amber-500" />
            <span className="font-bold text-2xl">ATLAS PUGUH</span>
          </Link>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-4">
                <CheckCircle2 className="h-8 w-8 text-emerald-600" />
              </div>
              <h2 className="text-xl font-semibold mb-2">Email Verified!</h2>
              <p className="text-muted-foreground mb-6">
                Your email has been verified. Redirecting you to your dashboard...
              </p>
              <Loader2 className="h-6 w-6 text-amber-500 animate-spin mx-auto" />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default VerifyEmail
