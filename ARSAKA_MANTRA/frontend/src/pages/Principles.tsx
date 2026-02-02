/**
 * Core Principles Page
 * Displays foundational rules in user-friendly language
 * Technical references (MANTRA-LAW-001) available via expandable sections
 */

import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Lock,
  FileText,
  Code,
  ScrollText,
  Layers,
  UserCheck,
  Building2,
  Info,
  Check,
  Ban,
  ArrowRight,
  Users,
  Bot,
  Settings,
  Grid3X3,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { DOMAINS, DOMAIN_LABELS, ASPECTS, ASPECT_LABELS } from '../shared/constants'

// Layer definitions - User-friendly language
const LAYERS = [
  {
    id: 0,
    name: 'Foundation Layer',
    subtitle: 'Core Principles',
    description: 'The fundamental rules that define how the system works. These rules never change.',
    color: 'bg-red-600',
    textColor: 'text-red-600',
    borderColor: 'border-red-200',
    bgLight: 'bg-red-50',
    icon: <Lock className="w-6 h-6" />,
    rules: [
      'These principles are permanent and cannot be changed',
      'No other rules can override or contradict these',
      'All decisions must follow these foundational rules',
      'Ensures consistency and trust across the system',
    ],
    mutability: 'Permanent',
    mutabilityDescription: 'Cannot be changed',
  },
  {
    id: 1,
    name: 'Decision Layer',
    subtitle: 'Architectural Decisions',
    description: 'The documented decisions about how your system should work. Once made, decisions are preserved forever.',
    color: 'bg-blue-600',
    textColor: 'text-blue-600',
    borderColor: 'border-blue-200',
    bgLight: 'bg-blue-50',
    icon: <FileText className="w-6 h-6" />,
    rules: [
      'Decisions are recorded permanently (you can add new versions, but never delete)',
      'New decisions can replace old ones by creating an updated version',
      'Decisions can link to each other (depends on, conflicts with, informed by)',
      'Organized into 4 categories with 16 topics',
    ],
    mutability: 'Add Only',
    mutabilityDescription: 'New versions replace old',
  },
  {
    id: 2,
    name: 'Implementation Layer',
    subtitle: 'Code & Configuration',
    description: 'The actual code, settings, and deployments that follow your decisions.',
    color: 'bg-green-600',
    textColor: 'text-green-600',
    borderColor: 'border-green-200',
    bgLight: 'bg-green-50',
    icon: <Code className="w-6 h-6" />,
    rules: [
      'Your code, configurations, and deployments',
      'Must follow the decisions from the layer above',
      'Can be changed and updated as needed',
      'Automatically checked against decision requirements',
    ],
    mutability: 'Flexible',
    mutabilityDescription: 'Can be changed freely',
  },
]

// Core Principles - User-friendly with technical references hidden
const CORE_PRINCIPLES = [
  {
    number: 1,
    title: 'AI Cannot Make Decisions',
    shortDescription: 'AI helps analyze and suggest, but only humans approve decisions',
    icon: Bot,
    iconColor: 'text-blue-600',
    iconBg: 'bg-blue-100',
    fullExplanation: 'AI tools can help you research, analyze potential conflicts, and suggest improvements. However, the final decision always requires human approval. No AI system can approve, reject, or create decisions on its own.',
    whatAICan: [
      'Read and search through existing decisions',
      'Detect potential conflicts between decisions',
      'Identify gaps in your decision coverage',
      'Generate warnings and suggestions',
      'Produce analysis reports for your review',
    ],
    whatAICannot: [
      'Create or approve any decision',
      'Reject or delete any decision',
      'Change the status of a decision',
      'Override your determinations',
    ],
    technicalRef: 'MANTRA-LAW-001 Section 6, Clauses 6.1-6.4',
  },
  {
    number: 2,
    title: 'Foundational Rules Cannot Change',
    shortDescription: 'These core principles are permanent and cannot be modified',
    icon: Lock,
    iconColor: 'text-red-600',
    iconBg: 'bg-red-100',
    fullExplanation: 'The foundational rules you see on this page are permanent. They cannot be changed, reinterpreted, or overridden by any other rules in the system. This ensures that the core principles remain consistent and trustworthy.',
    whatThisMeans: [
      'These principles are locked from the moment they were created',
      'No future updates can contradict these rules',
      'Other rules must work within these boundaries',
      'Any rule that contradicts these is automatically invalid',
    ],
    technicalRef: 'MANTRA-LAW-001 Section 10, Clauses 10.1-10.6',
  },
  {
    number: 3,
    title: 'Your Organization Owns Your Decisions',
    shortDescription: 'Only your organization can create and manage your decisions',
    icon: Building2,
    iconColor: 'text-purple-600',
    iconBg: 'bg-purple-100',
    fullExplanation: 'Your organization has complete ownership of its decisions. No external application, system, or other organization can create or modify your decisions. Applications can read and use your decisions, but only humans within your organization can create them.',
    whatThisMeans: [
      'Only your team members can create decisions',
      'External tools cannot modify your decisions',
      'Decisions from other organizations do not apply to you',
      'Applications use your decisions but cannot change them',
    ],
    technicalRef: 'MANTRA-LAW-001 Section 5, Clauses 5.1-5.3',
  },
  {
    number: 4,
    title: 'Decisions Must Follow the Standard Format',
    shortDescription: 'Valid decisions must include required information and structure',
    icon: FileText,
    iconColor: 'text-green-600',
    iconBg: 'bg-green-100',
    fullExplanation: 'For a decision to be valid, it must follow the standard format. This includes being assigned to the correct category, having a clear statement and rationale, and being created by a human. Decisions that do not follow this format are considered invalid.',
    requirements: [
      'Must belong to exactly one category (Domain)',
      'Must address exactly one topic (Aspect)',
      'Must have a human-written statement and rationale',
      'Must be created and approved by a person, not AI',
    ],
    technicalRef: 'MANTRA-LAW-001 Section 2, Clauses 2.1-2.3',
  },
]

// Authority Model - User-friendly language
const AUTHORITY_MODEL = {
  title: 'Who Can Do What',
  description: 'Clear roles define what each type of user can and cannot do in the system',
  roles: [
    {
      role: 'Team Members',
      description: 'People in your organization',
      icon: Users,
      permissions: [
        'Create new decisions',
        'Approve or reject decisions',
        'View all data and history',
        'Update organization settings',
      ],
      color: 'bg-green-100 text-green-800',
    },
    {
      role: 'AI Assistant',
      description: 'Automated analysis tools',
      icon: Bot,
      permissions: [
        'Read and search decisions',
        'Detect potential conflicts',
        'Identify coverage gaps',
        'Generate suggestions and reports',
      ],
      color: 'bg-blue-100 text-blue-800',
    },
    {
      role: 'System',
      description: 'Automated background processes',
      icon: Settings,
      permissions: [
        'Enforce the rules automatically',
        'Generate unique identifiers',
        'Keep the audit trail',
        'Validate requirements',
      ],
      color: 'bg-gray-100 text-gray-800',
    },
  ],
  prohibited: [
    'AI creating or approving decisions',
    'AI changing decision status',
    'AI overriding human choices',
    'Deleting approved decisions',
    'Modifying existing decision content',
    'Bypassing the approval process',
  ],
}

export default function Principles() {
  const [activeTab, setActiveTab] = useState<'principles' | 'layers' | 'authority' | 'categories'>('principles')
  const [expandedPrinciple, setExpandedPrinciple] = useState<number | null>(null)

  const togglePrinciple = (num: number) => {
    setExpandedPrinciple(expandedPrinciple === num ? null : num)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-100 rounded-lg">
            <ScrollText className="w-6 h-6 text-indigo-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Core Principles</h1>
            <p className="text-gray-500">The foundational rules that guide how decisions are managed</p>
          </div>
        </div>
      </div>

      {/* Friendly Notice */}
      <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Info className="w-6 h-6 text-indigo-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-indigo-800">About These Principles</h3>
            <p className="text-sm text-indigo-700 mt-1">
              These are the <strong>4 core principles</strong> that define how the decision management system works.
              They ensure consistency, maintain human control, and protect your organization's decisions.
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <nav className="flex gap-4">
          {[
            { id: 'principles', label: 'Core Principles', icon: ScrollText },
            { id: 'layers', label: 'How It Works', icon: Layers },
            { id: 'authority', label: 'Roles & Permissions', icon: UserCheck },
            { id: 'categories', label: 'Decision Categories', icon: Building2 },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === tab.id
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {/* Core Principles Tab - NEW USER-FRIENDLY VERSION */}
        {activeTab === 'principles' && (
          <div className="space-y-6">
            <p className="text-gray-600">
              These 4 principles define the foundation of how decisions are managed.
              Click on any principle to learn more about what it means for you.
            </p>

            <div className="space-y-4">
              {CORE_PRINCIPLES.map((principle) => (
                <div key={principle.number} className="border rounded-lg overflow-hidden">
                  {/* Principle Header - Always Visible */}
                  <button
                    onClick={() => togglePrinciple(principle.number)}
                    className="w-full px-4 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <div className={`p-2 rounded-lg ${principle.iconBg}`}>
                        <principle.icon className={`w-5 h-5 ${principle.iconColor}`} />
                      </div>
                      <div className="text-left">
                        <h3 className="font-semibold text-gray-900">
                          Principle {principle.number}: {principle.title}
                        </h3>
                        <p className="text-sm text-gray-500">{principle.shortDescription}</p>
                      </div>
                    </div>
                    {expandedPrinciple === principle.number ? (
                      <ChevronUp className="w-5 h-5 text-gray-400" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    )}
                  </button>

                  {/* Expanded Content */}
                  {expandedPrinciple === principle.number && (
                    <div className="px-4 pb-4 border-t bg-gray-50">
                      <div className="pt-4 space-y-4">
                        {/* Full Explanation */}
                        <div>
                          <h4 className="text-sm font-semibold text-gray-700 mb-2">What This Means</h4>
                          <p className="text-gray-600">{principle.fullExplanation}</p>
                        </div>

                        {/* What AI Can Do (only for principle 1) */}
                        {principle.whatAICan && (
                          <div className="grid md:grid-cols-2 gap-4">
                            <div>
                              <h4 className="text-sm font-semibold text-green-700 mb-2 flex items-center gap-2">
                                <Check className="w-4 h-4" />
                                What AI Can Do
                              </h4>
                              <ul className="space-y-1">
                                {principle.whatAICan.map((item, idx) => (
                                  <li key={idx} className="flex items-start gap-2 text-sm text-gray-600">
                                    <Check className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                                    {item}
                                  </li>
                                ))}
                              </ul>
                            </div>
                            <div>
                              <h4 className="text-sm font-semibold text-red-700 mb-2 flex items-center gap-2">
                                <Ban className="w-4 h-4" />
                                What AI Cannot Do
                              </h4>
                              <ul className="space-y-1">
                                {principle.whatAICannot?.map((item, idx) => (
                                  <li key={idx} className="flex items-start gap-2 text-sm text-gray-600">
                                    <Ban className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                                    {item}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        )}

                        {/* What This Means list (for principles 2, 3) */}
                        {principle.whatThisMeans && (
                          <div>
                            <h4 className="text-sm font-semibold text-gray-700 mb-2">In Practice</h4>
                            <ul className="space-y-1">
                              {principle.whatThisMeans.map((item, idx) => (
                                <li key={idx} className="flex items-start gap-2 text-sm text-gray-600">
                                  <Check className="w-4 h-4 text-indigo-500 flex-shrink-0 mt-0.5" />
                                  {item}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Requirements (for principle 4) */}
                        {principle.requirements && (
                          <div>
                            <h4 className="text-sm font-semibold text-gray-700 mb-2">Requirements</h4>
                            <ul className="space-y-1">
                              {principle.requirements.map((item, idx) => (
                                <li key={idx} className="flex items-start gap-2 text-sm text-gray-600">
                                  <Check className="w-4 h-4 text-indigo-500 flex-shrink-0 mt-0.5" />
                                  {item}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Technical Reference - Collapsed */}
                        <div className="pt-2 border-t border-gray-200">
                          <p className="text-xs text-gray-400">
                            Technical Reference: <span className="font-mono">{principle.technicalRef}</span>
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* AI Authority Highlight Box */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-indigo-200 rounded-lg p-6 text-center">
              <Bot className="w-12 h-12 text-indigo-600 mx-auto mb-2" />
              <h3 className="text-xl font-bold text-gray-800 mb-2">Remember: You Are Always in Control</h3>
              <p className="text-gray-600 max-w-2xl mx-auto">
                AI tools can help you analyze, search, and get suggestions - but every decision
                requires your explicit approval. The system is designed to assist you, not replace you.
              </p>
            </div>
          </div>
        )}

        {/* Layer Hierarchy Tab - RENAMED TO "How It Works" */}
        {activeTab === 'layers' && (
          <div className="space-y-6">
            <p className="text-gray-600">
              The system organizes information in three layers. Each layer has different rules
              about what can be changed and who can change it.
            </p>

            <div className="grid gap-6">
              {LAYERS.map((layer) => (
                <div
                  key={layer.id}
                  className={`border ${layer.borderColor} rounded-lg overflow-hidden`}
                >
                  <div className={`${layer.color} text-white px-4 py-3 flex items-center justify-between`}>
                    <div className="flex items-center gap-3">
                      {layer.icon}
                      <div>
                        <h3 className="font-semibold">{layer.name}</h3>
                        <p className="text-sm opacity-90">{layer.subtitle}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-sm font-medium">{layer.mutability}</span>
                      <p className="text-xs opacity-75">{layer.mutabilityDescription}</p>
                    </div>
                  </div>
                  <div className={`${layer.bgLight} p-4`}>
                    <p className="text-sm text-gray-600 mb-3">{layer.description}</p>
                    <h4 className={`text-sm font-semibold ${layer.textColor} mb-2`}>Key Points:</h4>
                    <ul className="space-y-2">
                      {layer.rules.map((rule, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                          <Check className={`w-4 h-4 ${layer.textColor} flex-shrink-0 mt-0.5`} />
                          {rule}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>

            {/* Layer Flow Diagram - Simplified */}
            <div className="bg-gray-50 rounded-lg p-6 mt-8">
              <h3 className="font-semibold text-gray-900 mb-4">How the Layers Work Together</h3>
              <div className="flex items-center justify-center gap-4 text-sm">
                <div className="text-center">
                  <div className="w-20 h-20 bg-red-600 rounded-lg flex items-center justify-center text-white mb-2">
                    <Lock className="w-8 h-8" />
                  </div>
                  <div className="font-medium text-gray-700">Foundation</div>
                  <div className="text-xs text-red-600">Permanent rules</div>
                </div>
                <ArrowRight className="w-8 h-8 text-gray-400" />
                <div className="text-center">
                  <div className="w-20 h-20 bg-blue-600 rounded-lg flex items-center justify-center text-white mb-2">
                    <FileText className="w-8 h-8" />
                  </div>
                  <div className="font-medium text-gray-700">Decisions</div>
                  <div className="text-xs text-blue-600">Add new versions</div>
                </div>
                <ArrowRight className="w-8 h-8 text-gray-400" />
                <div className="text-center">
                  <div className="w-20 h-20 bg-green-600 rounded-lg flex items-center justify-center text-white mb-2">
                    <Code className="w-8 h-8" />
                  </div>
                  <div className="font-medium text-gray-700">Code</div>
                  <div className="text-xs text-green-600">Freely changeable</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Authority Model Tab - RENAMED TO "Roles & Permissions" */}
        {activeTab === 'authority' && (
          <div className="space-y-6">
            <p className="text-gray-600">
              {AUTHORITY_MODEL.description}
            </p>

            {/* Roles */}
            <div className="grid gap-4 md:grid-cols-3">
              {AUTHORITY_MODEL.roles.map((role) => (
                <div key={role.role} className="border rounded-lg p-4">
                  <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium mb-2 ${role.color}`}>
                    <role.icon className="w-4 h-4" />
                    {role.role}
                  </div>
                  <p className="text-xs text-gray-500 mb-3">{role.description}</p>
                  <h4 className="text-xs font-semibold text-gray-400 uppercase mb-2">Can Do</h4>
                  <ul className="space-y-1">
                    {role.permissions.map((perm, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-gray-600">
                        <Check className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                        {perm}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>

            {/* Prohibited Actions - Simplified */}
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <h3 className="font-semibold text-red-800 mb-3 flex items-center gap-2">
                <Ban className="w-5 h-5" />
                Actions That Are Never Allowed
              </h3>
              <ul className="grid grid-cols-2 gap-2">
                {AUTHORITY_MODEL.prohibited.map((action, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-red-700">
                    <Ban className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                    {action}
                  </li>
                ))}
              </ul>
            </div>

            {/* AI Authority Box - Friendlier Language */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-indigo-200 rounded-lg p-6 text-center">
              <Bot className="w-12 h-12 text-indigo-600 mx-auto mb-2" />
              <h3 className="text-xl font-bold text-gray-800 mb-2">AI is Your Assistant, Not Your Boss</h3>
              <p className="text-gray-600 max-w-lg mx-auto mb-4">
                AI can help you analyze, search, and find potential issues - but it can never
                make decisions for you. Every decision requires your explicit approval.
              </p>
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-white rounded-full text-sm">
                <Users className="w-4 h-4 text-green-600" />
                <span className="font-medium text-gray-700">Humans decide</span>
                <span className="text-gray-400 mx-2">|</span>
                <Bot className="w-4 h-4 text-blue-600" />
                <span className="font-medium text-gray-700">AI assists</span>
              </div>
            </div>
          </div>
        )}

        {/* Domain Structure Tab - RENAMED TO "Decision Categories" */}
        {activeTab === 'categories' && (
          <div className="space-y-6">
            <p className="text-gray-600">
              Decisions are organized into 4 main categories, each covering different aspects of your system.
              This helps ensure nothing is overlooked and makes it easy to find related decisions.
            </p>

            {/* Category Cards - User-Friendly */}
            <div className="grid gap-4 md:grid-cols-2">
              {DOMAINS.map((domain) => {
                const colors: Record<string, { bg: string; text: string; border: string; headerBg: string }> = {
                  'INT': { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200', headerBg: 'bg-blue-600' },
                  'ARCH': { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200', headerBg: 'bg-purple-600' },
                  'CTL': { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200', headerBg: 'bg-red-600' },
                  'EVO': { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200', headerBg: 'bg-green-600' },
                }
                const descriptions: Record<string, { friendly: string; question: string }> = {
                  'INT': {
                    friendly: 'Why we are building this and what we want to achieve',
                    question: 'What problem are we solving? What does success look like?'
                  },
                  'ARCH': {
                    friendly: 'How the system is structured and where boundaries are',
                    question: 'How is it organized? What belongs where?'
                  },
                  'CTL': {
                    friendly: 'Rules, permissions, and risk management',
                    question: 'Who can do what? What are the risks?'
                  },
                  'EVO': {
                    friendly: 'How changes happen and systems evolve over time',
                    question: 'How do we make changes safely?'
                  },
                }
                const color = colors[domain]
                const desc = descriptions[domain]
                return (
                  <div key={domain} className={`border ${color.border} rounded-lg overflow-hidden`}>
                    <div className={`${color.headerBg} text-white px-4 py-3`}>
                      <Link
                        to={`/domain/${domain.toLowerCase()}`}
                        className="font-bold hover:underline"
                      >
                        {DOMAIN_LABELS[domain]}
                      </Link>
                      <p className="text-sm opacity-90 mt-1">{desc.friendly}</p>
                    </div>
                    <div className={`${color.bg} p-4`}>
                      <p className="text-sm text-gray-600 italic mb-3">"{desc.question}"</p>
                      <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Topics Covered</h4>
                      <div className="grid grid-cols-2 gap-2">
                        {ASPECTS[domain]?.map((aspect) => (
                          <div key={aspect} className="text-sm text-gray-700">
                            {ASPECT_LABELS[aspect]}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Summary Box */}
            <div className="bg-gray-50 rounded-lg p-6 text-center">
              <h3 className="font-semibold text-gray-900 mb-2">4 Categories, 16 Topics</h3>
              <p className="text-gray-600 text-sm max-w-xl mx-auto mb-4">
                Every decision fits into one category and one topic. This structure helps you
                organize decisions consistently and ensures comprehensive coverage of your system.
              </p>
              <Link
                to="/matrix"
                className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
              >
                <Grid3X3 className="w-5 h-5" />
                View Decision Matrix
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
