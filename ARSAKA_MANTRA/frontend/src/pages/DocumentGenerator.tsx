import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  docsApi,
  DocumentTypeInfo,
  GeneratedDocument,
  DocumentStats,
} from '@/shared/api'

export default function DocumentGenerator() {
  const [docTypes, setDocTypes] = useState<DocumentTypeInfo[]>([])
  const [stats, setStats] = useState<DocumentStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Form state
  const [selectedType, setSelectedType] = useState<string>('')
  const [title, setTitle] = useState('')
  const [companyName, setCompanyName] = useState('')
  const [domainFilter, setDomainFilter] = useState<string>('')
  const [scopeFilter, setScopeFilter] = useState('')
  const [maxDecisions, setMaxDecisions] = useState<number>(100)

  // Generated document
  const [generatedDoc, setGeneratedDoc] = useState<GeneratedDocument | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [types, statsData] = await Promise.all([
        docsApi.listTypes(),
        docsApi.getStats(),
      ])
      setDocTypes(types)
      setStats(statsData)
    } catch (err: any) {
      setError(err.message || 'Failed to load document types')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerate = async () => {
    if (!selectedType) {
      setError('Please select a document type')
      return
    }

    setGenerating(true)
    setError(null)
    try {
      const doc = await docsApi.generate({
        doc_type: selectedType,
        title: title || undefined,
        company_name: companyName || undefined,
        domain_filter: domainFilter || undefined,
        scope_filter: scopeFilter || undefined,
        max_decisions: maxDecisions,
        include_toc: true,
        include_metadata: true,
      })
      setGeneratedDoc(doc)
    } catch (err: any) {
      setError(err.message || 'Failed to generate document')
    } finally {
      setGenerating(false)
    }
  }

  const handleDownload = () => {
    if (!generatedDoc) return

    const blob = new Blob([generatedDoc.content], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${generatedDoc.title.replace(/\s+/g, '_')}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const handleCopy = () => {
    if (!generatedDoc) return
    navigator.clipboard.writeText(generatedDoc.content)
  }

  // Group doc types by phase
  const typesByPhase = docTypes.reduce((acc, t) => {
    if (!acc[t.phase]) acc[t.phase] = []
    acc[t.phase].push(t)
    return acc
  }, {} as Record<string, DocumentTypeInfo[]>)

  if (loading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-6">Document Generator</h1>
        <div className="animate-pulse space-y-4">
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Document Generator</h1>
          <p className="text-gray-500">Generate documentation from MANTRA decisions</p>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-4">
              <p className="text-3xl font-bold">{stats.total_document_types}</p>
              <p className="text-sm text-gray-500">Document Types</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-3xl font-bold">{Object.keys(stats.document_types_by_phase).length}</p>
              <p className="text-sm text-gray-500">Phases</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-3xl font-bold">{Object.keys(stats.document_types_by_audience).length}</p>
              <p className="text-sm text-gray-500">Audiences</p>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Generator Form */}
        <Card>
          <CardHeader>
            <CardTitle>Generate Document</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <div className="bg-red-50 text-red-600 p-3 rounded text-sm">{error}</div>
            )}

            <div>
              <Label>Document Type *</Label>
              <Select value={selectedType} onValueChange={setSelectedType}>
                <SelectTrigger>
                  <SelectValue placeholder="Select document type..." />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(typesByPhase).map(([phase, types]) => (
                    <div key={phase}>
                      <div className="px-2 py-1 text-xs font-semibold text-gray-500 bg-gray-100">
                        {phase}
                      </div>
                      {types.map((t) => (
                        <SelectItem key={t.type} value={t.type}>
                          {t.name} ({t.primary_audience})
                        </SelectItem>
                      ))}
                    </div>
                  ))}
                </SelectContent>
              </Select>
              {selectedType && (
                <p className="text-xs text-gray-500 mt-1">
                  {docTypes.find(t => t.type === selectedType)?.description}
                </p>
              )}
            </div>

            <div>
              <Label>Custom Title (optional)</Label>
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g., My Project PRD"
              />
            </div>

            <div>
              <Label>Company Name (optional)</Label>
              <Input
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="e.g., Acme Corp"
              />
            </div>

            <div>
              <Label>Domain Filter</Label>
              <Select value={domainFilter} onValueChange={setDomainFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="All domains" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All domains</SelectItem>
                  <SelectItem value="INT">INT - Intent & Direction</SelectItem>
                  <SelectItem value="ARCH">ARCH - Architecture</SelectItem>
                  <SelectItem value="CTL">CTL - Control & Policy</SelectItem>
                  <SelectItem value="EVO">EVO - Evolution</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Scope Filter (optional)</Label>
              <Input
                value={scopeFilter}
                onChange={(e) => setScopeFilter(e.target.value)}
                placeholder="e.g., frontend/*, backend/api/*"
              />
            </div>

            <div>
              <Label>Max Decisions</Label>
              <Input
                type="number"
                value={maxDecisions}
                onChange={(e) => setMaxDecisions(Number(e.target.value))}
                min={1}
                max={1000}
              />
            </div>

            <Button
              onClick={handleGenerate}
              disabled={!selectedType || generating}
              className="w-full"
            >
              {generating ? 'Generating...' : 'Generate Document'}
            </Button>
          </CardContent>
        </Card>

        {/* Document Types Reference */}
        <Card>
          <CardHeader>
            <CardTitle>Available Document Types</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 max-h-[500px] overflow-y-auto">
              {Object.entries(typesByPhase).map(([phase, types]) => (
                <div key={phase}>
                  <h4 className="font-semibold text-sm text-gray-700 mb-2">{phase}</h4>
                  <div className="space-y-2">
                    {types.map((t) => (
                      <div
                        key={t.type}
                        className={`p-2 rounded border cursor-pointer hover:bg-gray-50 ${
                          selectedType === t.type ? 'border-blue-500 bg-blue-50' : ''
                        }`}
                        onClick={() => setSelectedType(t.type)}
                      >
                        <div className="font-medium text-sm">{t.name}</div>
                        <div className="text-xs text-gray-500">{t.primary_audience}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Generated Document */}
      {generatedDoc && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>{generatedDoc.title}</CardTitle>
              <p className="text-sm text-gray-500 mt-1">
                {generatedDoc.word_count} words | {generatedDoc.section_count} sections | {generatedDoc.decision_count} decisions
              </p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={handleCopy}>Copy</Button>
              <Button onClick={handleDownload}>Download</Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="bg-gray-50 rounded p-4 max-h-[600px] overflow-y-auto">
              <pre className="whitespace-pre-wrap text-sm font-mono">{generatedDoc.content}</pre>
            </div>
            <div className="mt-4 text-xs text-gray-500">
              <p>Generated: {new Date(generatedDoc.generated_at).toLocaleString()}</p>
              <p>Source decisions: {generatedDoc.source_decisions.join(', ')}</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
