/**
 * Security Dashboard - User Security Overview
 *
 * Shows security-related information for the current user:
 * - Recent login activity
 * - Active sessions
 * - Security settings
 * - Account status
 */

import { useQuery } from '@tanstack/react-query'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Shield,
  ShieldCheck,
  ShieldAlert,
  Key,
  Lock,
  Unlock,
  Monitor,
  MapPin,
  AlertTriangle,
  CheckCircle,
  XCircle,
  LogOut,
  RefreshCw,
  Eye,
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

// Types
interface LoginActivity {
  id: string
  timestamp: string
  ipAddress: string
  location?: string
  device: string
  browser: string
  status: 'success' | 'failure' | 'blocked'
  reason?: string
}

interface ActiveSession {
  id: string
  device: string
  browser: string
  ipAddress: string
  location?: string
  lastActive: string
  isCurrent: boolean
}

interface SecuritySettings {
  twoFactorEnabled: boolean
  passwordLastChanged?: string
  emailVerified: boolean
  accountLockedUntil?: string
  failedLoginAttempts: number
}

// Mock data for development
const mockLoginActivity: LoginActivity[] = [
  {
    id: '1',
    timestamp: new Date().toISOString(),
    ipAddress: '192.168.1.100',
    location: 'Jakarta, Indonesia',
    device: 'Windows 10',
    browser: 'Chrome 120',
    status: 'success',
  },
  {
    id: '2',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    ipAddress: '192.168.1.100',
    location: 'Jakarta, Indonesia',
    device: 'Windows 10',
    browser: 'Chrome 120',
    status: 'success',
  },
  {
    id: '3',
    timestamp: new Date(Date.now() - 86400000).toISOString(),
    ipAddress: '103.23.45.67',
    location: 'Unknown',
    device: 'Unknown',
    browser: 'Unknown',
    status: 'failure',
    reason: 'Invalid password',
  },
]

const mockActiveSessions: ActiveSession[] = [
  {
    id: '1',
    device: 'Windows 10',
    browser: 'Chrome 120',
    ipAddress: '192.168.1.100',
    location: 'Jakarta, Indonesia',
    lastActive: new Date().toISOString(),
    isCurrent: true,
  },
]

const mockSecuritySettings: SecuritySettings = {
  twoFactorEnabled: false,
  passwordLastChanged: new Date(Date.now() - 30 * 86400000).toISOString(),
  emailVerified: true,
  failedLoginAttempts: 0,
}

export function SecurityDashboard() {
  // In production, these would be API calls
  const { data: loginActivity = mockLoginActivity } = useQuery({
    queryKey: ['security', 'login-activity'],
    queryFn: async () => {
      // TODO: Implement API call
      // return api.get<LoginActivity[]>('/api/v1/security/login-activity')
      return mockLoginActivity
    },
  })

  const { data: sessions = mockActiveSessions } = useQuery({
    queryKey: ['security', 'sessions'],
    queryFn: async () => {
      // TODO: Implement API call
      return mockActiveSessions
    },
  })

  const { data: settings = mockSecuritySettings } = useQuery({
    queryKey: ['security', 'settings'],
    queryFn: async () => {
      // TODO: Implement API call
      return mockSecuritySettings
    },
  })

  const handleRevokeSession = async (sessionId: string) => {
    // TODO: Implement session revocation
    console.log('Revoke session:', sessionId)
  }

  const handleRevokeAllSessions = async () => {
    // TODO: Implement revoke all sessions
    console.log('Revoke all sessions')
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-card rounded-lg border border-l-4 border-l-primary p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Shield className="h-6 w-6 text-primary" />
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold">Security Dashboard</h1>
                {settings.twoFactorEnabled ? (
                  <Badge variant="default">2FA Enabled</Badge>
                ) : (
                  <Badge variant="warning">2FA Disabled</Badge>
                )}
              </div>
              <p className="text-muted-foreground mt-1">
                Monitor your account security and manage active sessions
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Security Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Account Status */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-lg ${
                settings.accountLockedUntil
                  ? 'bg-red-100'
                  : 'bg-green-100'
              }`}>
                {settings.accountLockedUntil ? (
                  <Lock className="h-6 w-6 text-red-600" />
                ) : (
                  <Unlock className="h-6 w-6 text-green-600" />
                )}
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Account Status</p>
                <p className="text-lg font-semibold">
                  {settings.accountLockedUntil ? 'Locked' : 'Active'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 2FA Status */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-lg ${
                settings.twoFactorEnabled
                  ? 'bg-green-100'
                  : 'bg-yellow-100'
              }`}>
                {settings.twoFactorEnabled ? (
                  <ShieldCheck className="h-6 w-6 text-green-600" />
                ) : (
                  <ShieldAlert className="h-6 w-6 text-yellow-600" />
                )}
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Two-Factor Auth</p>
                <p className="text-lg font-semibold">
                  {settings.twoFactorEnabled ? 'Enabled' : 'Disabled'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Password Age */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <Key className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Password Changed</p>
                <p className="text-lg font-semibold">
                  {settings.passwordLastChanged
                    ? formatDistanceToNow(new Date(settings.passwordLastChanged), { addSuffix: true })
                    : 'Never'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Active Sessions */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-purple-100 rounded-lg">
                <Monitor className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Active Sessions</p>
                <p className="text-lg font-semibold">{sessions.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Account Lockout Warning */}
      {settings.failedLoginAttempts > 0 && (
        <Card className="border-yellow-500 border-l-4">
          <CardContent className="pt-6">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-yellow-100 rounded-lg">
                <AlertTriangle className="h-6 w-6 text-yellow-600" />
              </div>
              <div>
                <h3 className="font-semibold">Failed Login Attempts Detected</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  There have been <strong>{settings.failedLoginAttempts}</strong> failed login
                  attempt(s) on your account. If this wasn't you, consider changing your password.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Login Activity */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg">Recent Login Activity</CardTitle>
                <CardDescription>Your last login attempts</CardDescription>
              </div>
              <Button variant="outline" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {loginActivity.map((activity) => (
                <div
                  key={activity.id}
                  className="flex items-start justify-between p-3 bg-muted/50 rounded-lg"
                >
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-lg ${
                      activity.status === 'success'
                        ? 'bg-green-100'
                        : activity.status === 'blocked'
                        ? 'bg-yellow-100'
                        : 'bg-red-100'
                    }`}>
                      {activity.status === 'success' ? (
                        <CheckCircle className="h-4 w-4 text-green-600" />
                      ) : activity.status === 'blocked' ? (
                        <ShieldAlert className="h-4 w-4 text-yellow-600" />
                      ) : (
                        <XCircle className="h-4 w-4 text-red-600" />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{activity.browser}</span>
                        <span className="text-muted-foreground">on</span>
                        <span className="font-medium">{activity.device}</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                        <MapPin className="h-3 w-3" />
                        <span>{activity.location || 'Unknown location'}</span>
                        <span>({activity.ipAddress})</span>
                      </div>
                      {activity.reason && (
                        <p className="text-sm text-red-600 mt-1">{activity.reason}</p>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge variant={
                      activity.status === 'success'
                        ? 'default'
                        : activity.status === 'blocked'
                        ? 'warning'
                        : 'destructive'
                    }>
                      {activity.status}
                    </Badge>
                    <p className="text-xs text-muted-foreground mt-1">
                      {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Active Sessions */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg">Active Sessions</CardTitle>
                <CardDescription>Devices currently logged in</CardDescription>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRevokeAllSessions}
              >
                <LogOut className="h-4 w-4 mr-2" />
                Revoke All
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  className={`flex items-start justify-between p-3 rounded-lg ${
                    session.isCurrent ? 'bg-primary/5 border border-primary/20' : 'bg-muted/50'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="p-2 bg-muted rounded-lg">
                      <Monitor className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{session.browser}</span>
                        {session.isCurrent && (
                          <Badge variant="default" className="text-xs">Current</Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">{session.device}</p>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                        <MapPin className="h-3 w-3" />
                        <span>{session.location || session.ipAddress}</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground">
                      Active {formatDistanceToNow(new Date(session.lastActive), { addSuffix: true })}
                    </p>
                    {!session.isCurrent && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="mt-1 h-7 text-red-600"
                        onClick={() => handleRevokeSession(session.id)}
                      >
                        Revoke
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Security Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Security Recommendations</CardTitle>
          <CardDescription>Steps to improve your account security</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* 2FA Recommendation */}
            {!settings.twoFactorEnabled && (
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-yellow-100 rounded-lg">
                    <ShieldAlert className="h-5 w-5 text-yellow-600" />
                  </div>
                  <div>
                    <p className="font-medium">Enable Two-Factor Authentication</p>
                    <p className="text-sm text-muted-foreground">
                      Add an extra layer of security to your account
                    </p>
                  </div>
                </div>
                <Button variant="outline">Enable 2FA</Button>
              </div>
            )}

            {/* Password Age Warning */}
            {settings.passwordLastChanged &&
              new Date(settings.passwordLastChanged) < new Date(Date.now() - 90 * 86400000) && (
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-yellow-100 rounded-lg">
                    <Key className="h-5 w-5 text-yellow-600" />
                  </div>
                  <div>
                    <p className="font-medium">Update Your Password</p>
                    <p className="text-sm text-muted-foreground">
                      Your password hasn't been changed in over 90 days
                    </p>
                  </div>
                </div>
                <Button variant="outline">Change Password</Button>
              </div>
            )}

            {/* Email Verification */}
            {!settings.emailVerified && (
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-red-100 rounded-lg">
                    <AlertTriangle className="h-5 w-5 text-red-600" />
                  </div>
                  <div>
                    <p className="font-medium">Verify Your Email Address</p>
                    <p className="text-sm text-muted-foreground">
                      Verify your email to secure your account
                    </p>
                  </div>
                </div>
                <Button variant="outline">Resend Verification</Button>
              </div>
            )}

            {/* All Good */}
            {settings.twoFactorEnabled &&
              settings.emailVerified &&
              settings.passwordLastChanged &&
              new Date(settings.passwordLastChanged) >= new Date(Date.now() - 90 * 86400000) && (
              <div className="flex items-center gap-3 p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="p-2 bg-green-100 rounded-lg">
                  <ShieldCheck className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="font-medium text-green-800">Your account is secure</p>
                  <p className="text-sm text-green-600">
                    All security recommendations have been followed
                  </p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Privacy Note */}
      <Card className="bg-muted/30">
        <CardContent className="pt-6">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-primary/10 rounded-lg">
              <Eye className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold">Your Privacy Matters</h3>
              <p className="text-sm text-muted-foreground mt-1">
                We take your data security seriously. Your login activity is logged for security
                purposes and is only accessible by you and our security team. We never share
                your personal data with third parties without your consent. For more information,
                see our{' '}
                <a href="/privacy" className="text-primary underline">
                  Privacy Policy
                </a>
                .
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default SecurityDashboard
