/**
 * ATLAS_PUGUH - Landing Page
 * Marketing page with hero, features, and pricing
 */

import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Scale,
  Shield,
  Workflow,
  BarChart3,
  Building2,
  Check,
  ArrowRight,
  Zap,
} from 'lucide-react'

const features = [
  {
    icon: Scale,
    title: 'Decision Engine',
    description: 'Constitutional law system for AI-assisted decision making with rule evaluation and policy enforcement.',
    color: 'text-amber-500',
    bgColor: 'bg-amber-50',
  },
  {
    icon: Shield,
    title: 'Identity & Access',
    description: 'Enterprise-grade IAM with role-based permissions, service accounts, and audit trails.',
    color: 'text-blue-500',
    bgColor: 'bg-blue-50',
  },
  {
    icon: Workflow,
    title: 'Workflow Orchestration',
    description: 'Multi-step approval workflows with escalation, delegation, and automated routing.',
    color: 'text-emerald-500',
    bgColor: 'bg-emerald-50',
  },
  {
    icon: Building2,
    title: 'Multi-Tenant Architecture',
    description: 'Complete tenant isolation with per-tenant rules, workflows, and data separation.',
    color: 'text-violet-500',
    bgColor: 'bg-violet-50',
  },
  {
    icon: BarChart3,
    title: 'Audit & Control',
    description: 'Real-time audit logging, event tracking, and compliance reporting.',
    color: 'text-slate-500',
    bgColor: 'bg-slate-50',
  },
]

const plans = [
  {
    name: 'Free',
    price: 'Rp 0',
    period: '/month',
    description: 'For individuals and small teams getting started',
    features: [
      '1 Project',
      '1,000 decisions/month',
      '3 Team members',
      'Basic support',
      '7-day audit retention',
    ],
    cta: 'Get Started',
    popular: false,
  },
  {
    name: 'Starter',
    price: 'Rp 290K',
    period: '/month',
    description: 'For growing teams with more complex needs',
    features: [
      '5 Projects',
      '10,000 decisions/month',
      '10 Team members',
      'Email support',
      '30-day audit retention',
      'Custom rules',
    ],
    cta: 'Start Free Trial',
    popular: true,
  },
  {
    name: 'Pro',
    price: 'Rp 990K',
    period: '/month',
    description: 'For organizations requiring advanced features',
    features: [
      'Unlimited Projects',
      '100,000 decisions/month',
      'Unlimited team members',
      'Priority support',
      '1-year audit retention',
      'API access',
      'Custom workflows',
    ],
    cta: 'Start Free Trial',
    popular: false,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: '',
    description: 'For large organizations with specific requirements',
    features: [
      'Everything in Pro',
      'Unlimited decisions',
      'SSO/SAML',
      'Dedicated support',
      'Custom retention',
      'SLA guarantee',
      'On-premise option',
    ],
    cta: 'Contact Sales',
    popular: false,
  },
]

export function Landing() {
  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Scale className="h-8 w-8 text-amber-500" />
            <span className="font-bold text-xl">ATLAS PUGUH</span>
          </div>
          <nav className="hidden md:flex items-center gap-6">
            <a href="#features" className="text-muted-foreground hover:text-foreground transition-colors">
              Features
            </a>
            <a href="#pricing" className="text-muted-foreground hover:text-foreground transition-colors">
              Pricing
            </a>
            <a href="http://31.97.111.175:3002/docs/" target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-foreground transition-colors">
              Docs
            </a>
            <a href="#about" className="text-muted-foreground hover:text-foreground transition-colors">
              About
            </a>
          </nav>
          <div className="flex items-center gap-3">
            <Link to="/login">
              <Button variant="ghost">Login</Button>
            </Link>
            <Link to="/register">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 md:py-32">
        <div className="container mx-auto px-4 text-center">
          <div className="inline-flex items-center gap-2 bg-amber-50 text-amber-700 px-4 py-2 rounded-full text-sm font-medium mb-6">
            <Zap className="h-4 w-4" />
            Constitutional Law for AI Decisions
          </div>
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6 max-w-4xl mx-auto">
            Govern Your AI Decisions with{' '}
            <span className="text-amber-500">Transparency & Control</span>
          </h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            ATLAS PUGUH is an enterprise decision engine that enforces constitutional laws
            on AI-assisted decisions, ensuring compliance, auditability, and trust.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/register">
              <Button size="lg" className="gap-2">
                Start Free <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <a href="#features">
              <Button size="lg" variant="outline">
                Learn More
              </Button>
            </a>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mt-16 max-w-3xl mx-auto">
            {[
              { value: '99.9%', label: 'Uptime SLA' },
              { value: '<50ms', label: 'Decision Latency' },
              { value: '100%', label: 'Audit Coverage' },
              { value: '24/7', label: 'Support' },
            ].map((stat, i) => (
              <div key={i} className="text-center">
                <div className="text-3xl font-bold text-amber-500">{stat.value}</div>
                <div className="text-sm text-muted-foreground">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 bg-slate-50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">5 Core Services</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              A complete platform for enterprise decision governance with modular, scalable architecture.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {features.map((feature, i) => (
              <Card key={i} className="border-0 shadow-sm hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className={`w-12 h-12 rounded-lg ${feature.bgColor} flex items-center justify-center mb-4`}>
                    <feature.icon className={`h-6 w-6 ${feature.color}`} />
                  </div>
                  <CardTitle className="text-lg">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-sm">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Built for Enterprise Use Cases</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              From financial approvals to content moderation, PUGUH handles it all.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            {[
              {
                title: 'Financial Approvals',
                description: 'Automate expense approvals with configurable thresholds and multi-level sign-off.',
              },
              {
                title: 'Content Moderation',
                description: 'Apply consistent content policies with AI-assisted review and human oversight.',
              },
              {
                title: 'Access Requests',
                description: 'Streamline access provisioning with role-based rules and audit compliance.',
              },
            ].map((useCase, i) => (
              <div key={i} className="text-center p-6">
                <div className="w-16 h-16 rounded-full bg-amber-100 flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-amber-500">{i + 1}</span>
                </div>
                <h3 className="font-semibold mb-2">{useCase.title}</h3>
                <p className="text-sm text-muted-foreground">{useCase.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 bg-slate-50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Simple, Transparent Pricing</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Start free and scale as you grow. All plans include core features.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
            {plans.map((plan, i) => (
              <Card
                key={i}
                className={`relative ${plan.popular ? 'border-amber-500 border-2' : 'border'}`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-amber-500 text-white px-3 py-1 rounded-full text-xs font-medium">
                    Most Popular
                  </div>
                )}
                <CardHeader>
                  <CardTitle className="text-lg">{plan.name}</CardTitle>
                  <div className="mt-2">
                    <span className="text-3xl font-bold">{plan.price}</span>
                    <span className="text-muted-foreground">{plan.period}</span>
                  </div>
                  <CardDescription className="mt-2">{plan.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 mb-6">
                    {plan.features.map((feature, j) => (
                      <li key={j} className="flex items-center gap-2 text-sm">
                        <Check className="h-4 w-4 text-emerald-500 flex-shrink-0" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                  <Link to="/register">
                    <Button
                      className="w-full"
                      variant={plan.popular ? 'default' : 'outline'}
                    >
                      {plan.cta}
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to Get Started?</h2>
          <p className="text-muted-foreground mb-8 max-w-xl mx-auto">
            Join organizations that trust ATLAS PUGUH for their decision governance needs.
          </p>
          <Link to="/register">
            <Button size="lg" className="gap-2">
              Create Free Account <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer id="about" className="border-t py-12 bg-slate-900 text-slate-300">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-2 text-white mb-4">
                <Scale className="h-6 w-6 text-amber-500" />
                <span className="font-bold">ATLAS PUGUH</span>
              </div>
              <p className="text-sm text-slate-400">
                Constitutional law system for AI-assisted decision making.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Product</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
                <li><a href="#pricing" className="hover:text-white transition-colors">Pricing</a></li>
                <li><a href="http://31.97.111.175:3002/docs/" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">Documentation</a></li>
                <li><a href="http://31.97.111.175:3002/docs/api-reference" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">API Reference</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Company</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white transition-colors">About</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Blog</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Careers</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Contact</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Legal</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white transition-colors">Privacy Policy</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Terms of Service</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Security</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-slate-800 mt-8 pt-8 text-center text-sm text-slate-400">
            &copy; {new Date().getFullYear()} ATLAS PUGUH. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Landing
