/**
 * HelpSidebar - Slide-out help panel
 * Shows contextual help articles based on current page
 */

import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  BookOpen,
  ExternalLink,
  Search,
  X,
  HelpCircle,
  Lightbulb,
} from 'lucide-react'
import { useHelpStore } from '@/stores/helpStore'
import { getArticlesForPage, HelpArticle } from '@/data/helpContent'

interface HelpArticleCardProps {
  article: HelpArticle
}

function HelpArticleCard({ article }: HelpArticleCardProps) {
  return (
    <div className="p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors">
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-md bg-amber-100 text-amber-600">
          <Lightbulb className="h-4 w-4" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-sm mb-1">{article.title}</h4>
          <p className="text-xs text-muted-foreground whitespace-pre-line line-clamp-4">
            {article.content.split('\n').slice(0, 3).join('\n')}
          </p>

          {/* Tags */}
          <div className="flex flex-wrap gap-1 mt-2">
            {article.tags.slice(0, 3).map((tag) => (
              <Badge key={tag} variant="secondary" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>

          {/* Docs link */}
          {article.docsUrl && (
            <a
              href={article.docsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-amber-600 hover:text-amber-700 mt-2"
            >
              Read more in docs
              <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </div>
      </div>
    </div>
  )
}

export function HelpSidebar() {
  const location = useLocation()
  const {
    isOpen,
    setOpen,
    currentPage,
    setCurrentPage,
    searchQuery,
    setSearchQuery,
  } = useHelpStore()

  // Update current page when location changes
  useEffect(() => {
    setCurrentPage(location.pathname)
  }, [location.pathname, setCurrentPage])

  // Get relevant articles for current page
  const articles = getArticlesForPage(currentPage, searchQuery)

  // Get page title for display
  const getPageTitle = () => {
    if (currentPage.includes('/iam')) return 'IAM'
    if (currentPage.includes('/tenant')) return 'Tenant'
    if (currentPage.includes('/decision')) return 'Decision'
    if (currentPage.includes('/workflow')) return 'Workflow'
    if (currentPage.includes('/control')) return 'Control'
    if (currentPage.includes('/billing')) return 'Billing'
    return 'Dashboard'
  }

  return (
    <Sheet open={isOpen} onOpenChange={setOpen}>
      <SheetContent side="right" className="w-[400px] sm:w-[450px] p-0">
        <div className="flex flex-col h-full">
          {/* Header */}
          <SheetHeader className="p-4 border-b">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-md bg-amber-100">
                  <HelpCircle className="h-5 w-5 text-amber-600" />
                </div>
                <div>
                  <SheetTitle className="text-lg">Help & Support</SheetTitle>
                  <p className="text-xs text-muted-foreground">
                    Context: {getPageTitle()}
                  </p>
                </div>
              </div>
            </div>
          </SheetHeader>

          {/* Search */}
          <div className="p-4 border-b">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search help articles..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 pr-9"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>

          {/* Articles */}
          <ScrollArea className="flex-1">
            <div className="p-4 space-y-3">
              {articles.length > 0 ? (
                articles.map((article) => (
                  <HelpArticleCard key={article.id} article={article} />
                ))
              ) : (
                <div className="text-center py-8">
                  <HelpCircle className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
                  <p className="text-muted-foreground text-sm">
                    {searchQuery
                      ? 'No articles match your search'
                      : 'No help articles for this page'}
                  </p>
                  {searchQuery && (
                    <Button
                      variant="link"
                      size="sm"
                      onClick={() => setSearchQuery('')}
                    >
                      Clear search
                    </Button>
                  )}
                </div>
              )}
            </div>
          </ScrollArea>

          {/* Footer */}
          <div className="border-t p-4">
            <div className="space-y-2">
              <a
                href="http://31.97.111.175:3002/docs/"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 p-3 rounded-lg border hover:bg-accent transition-colors"
              >
                <BookOpen className="h-5 w-5 text-amber-600" />
                <div className="flex-1">
                  <p className="text-sm font-medium">Full Documentation</p>
                  <p className="text-xs text-muted-foreground">
                    Browse all guides and tutorials
                  </p>
                </div>
                <ExternalLink className="h-4 w-4 text-muted-foreground" />
              </a>

              <div className="text-center">
                <a
                  href="mailto:support@atlashub.com"
                  className="text-xs text-muted-foreground hover:text-foreground"
                >
                  Need more help? Contact support@atlashub.com
                </a>
              </div>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  )
}
