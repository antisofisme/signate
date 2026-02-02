/**
 * Product Switcher Page
 *
 * Displays available products in the PUGUH platform.
 * Users can see their subscriptions and launch products.
 *
 * Inspired by Google Workspace app launcher / Microsoft 365 app switcher.
 */

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  CheckCircle2,
  ExternalLink,
  Lock,
  Sparkles,
  Clock,
  ArrowRight,
  Layers,
} from 'lucide-react'
import { api } from '@/lib/api-client'

// Types
interface ProductFeatures {
  mcpIntegration: boolean
  apiAccess: boolean
  ssoSupport: boolean
  webhooks: boolean
  customBranding: boolean
}

interface ProductInfo {
  productId: string
  code: string
  name: string
  description: string | null
  tagline: string | null
  iconUrl: string | null
  logoUrl: string | null
  colorPrimary: string | null
  appUrl: string | null
  docsUrl: string | null
  status: string
  isFeatured: boolean
  features: ProductFeatures
  displayOrder: number
}

interface ProductWithSubscription {
  product: ProductInfo
  isSubscribed: boolean
  subscriptionStatus: string | null
  planId: string | null
  trialDaysRemaining: number
}

interface ListProductsResponse {
  products: ProductWithSubscription[]
  subscribedCount: number
  totalCount: number
}

// Product Card Component
function ProductCard({ item }: { item: ProductWithSubscription }) {
  const { product, isSubscribed, planId, trialDaysRemaining } = item
  const isComingSoon = product.status === 'coming_soon'
  const isBeta = product.status === 'beta'
  const inTrial = trialDaysRemaining > 0

  const handleLaunch = () => {
    if (product.appUrl) {
      // In production, would pass JWT token for SSO
      window.open(product.appUrl, '_blank')
    }
  }

  return (
    <Card
      className={`relative overflow-hidden transition-all hover:shadow-lg ${
        isSubscribed ? 'border-primary/50' : 'border-muted'
      } ${isComingSoon ? 'opacity-75' : ''}`}
    >
      {/* Color accent bar */}
      <div
        className="absolute top-0 left-0 right-0 h-1"
        style={{ backgroundColor: product.colorPrimary || '#6366f1' }}
      />

      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            {/* Product icon or initial */}
            <div
              className="flex h-12 w-12 items-center justify-center rounded-lg text-white text-lg font-bold"
              style={{ backgroundColor: product.colorPrimary || '#6366f1' }}
            >
              {product.iconUrl ? (
                <img src={product.iconUrl} alt={product.name} className="h-8 w-8" />
              ) : (
                product.name.charAt(0)
              )}
            </div>

            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                {product.name}
                {product.isFeatured && (
                  <Sparkles className="h-4 w-4 text-yellow-500" />
                )}
              </CardTitle>
              {product.tagline && (
                <p className="text-xs text-muted-foreground">{product.tagline}</p>
              )}
            </div>
          </div>

          {/* Status badges */}
          <div className="flex flex-col items-end gap-1">
            {isSubscribed && (
              <Badge variant="default" className="gap-1">
                <CheckCircle2 className="h-3 w-3" />
                {inTrial ? `Trial (${trialDaysRemaining}d)` : planId?.toUpperCase() || 'ACTIVE'}
              </Badge>
            )}
            {isBeta && (
              <Badge variant="secondary">BETA</Badge>
            )}
            {isComingSoon && (
              <Badge variant="outline" className="gap-1">
                <Clock className="h-3 w-3" />
                Coming Soon
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="pb-4">
        {product.description && (
          <CardDescription className="mb-4 line-clamp-2">
            {product.description}
          </CardDescription>
        )}

        {/* Features */}
        <div className="flex flex-wrap gap-1 mb-4">
          {product.features.mcpIntegration && (
            <Badge variant="outline" className="text-xs">MCP</Badge>
          )}
          {product.features.apiAccess && (
            <Badge variant="outline" className="text-xs">API</Badge>
          )}
          {product.features.webhooks && (
            <Badge variant="outline" className="text-xs">Webhooks</Badge>
          )}
          {product.features.ssoSupport && (
            <Badge variant="outline" className="text-xs">SSO</Badge>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          {isSubscribed && !isComingSoon ? (
            <Button
              onClick={handleLaunch}
              className="flex-1 gap-2"
              style={{ backgroundColor: product.colorPrimary || undefined }}
            >
              Launch
              <ExternalLink className="h-4 w-4" />
            </Button>
          ) : isComingSoon ? (
            <Button variant="outline" disabled className="flex-1 gap-2">
              <Lock className="h-4 w-4" />
              Coming Soon
            </Button>
          ) : (
            <Button variant="outline" className="flex-1 gap-2">
              Subscribe
              <ArrowRight className="h-4 w-4" />
            </Button>
          )}

          {product.docsUrl && (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => window.open(product.docsUrl!, '_blank')}
            >
              <ExternalLink className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

// Loading skeleton
function ProductCardSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <Skeleton className="h-12 w-12 rounded-lg" />
            <div>
              <Skeleton className="h-5 w-24 mb-1" />
              <Skeleton className="h-3 w-32" />
            </div>
          </div>
          <Skeleton className="h-5 w-16" />
        </div>
      </CardHeader>
      <CardContent className="pb-4">
        <Skeleton className="h-10 w-full mb-4" />
        <div className="flex gap-1 mb-4">
          <Skeleton className="h-5 w-12" />
          <Skeleton className="h-5 w-12" />
          <Skeleton className="h-5 w-12" />
        </div>
        <Skeleton className="h-9 w-full" />
      </CardContent>
    </Card>
  )
}

// Main Component
export default function ProductSwitcher() {
  const [products, setProducts] = useState<ProductWithSubscription[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadProducts()
  }, [])

  async function loadProducts() {
    try {
      setLoading(true)
      const response = await api.get<ListProductsResponse>('/products')
      setProducts(response.data.products)
    } catch (err) {
      setError('Failed to load products')
      console.error('Error loading products:', err)
    } finally {
      setLoading(false)
    }
  }

  // Separate subscribed and available products
  const subscribedProducts = products.filter(p => p.isSubscribed)
  const availableProducts = products.filter(p => !p.isSubscribed)

  return (
    <div className="container max-w-6xl py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Layers className="h-5 w-5" />
          </div>
          <h1 className="text-2xl font-bold">Products</h1>
        </div>
        <p className="text-muted-foreground">
          Manage your PUGUH platform products and subscriptions
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-destructive/10 text-destructive rounded-lg">
          {error}
        </div>
      )}

      {/* Subscribed Products */}
      {(loading || subscribedProducts.length > 0) && (
        <section className="mb-10">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-500" />
            Your Products
          </h2>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {loading ? (
              <>
                <ProductCardSkeleton />
                <ProductCardSkeleton />
              </>
            ) : (
              subscribedProducts.map((item) => (
                <ProductCard key={item.product.productId} item={item} />
              ))
            )}
          </div>
        </section>
      )}

      {/* Available Products */}
      {(loading || availableProducts.length > 0) && (
        <section>
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-yellow-500" />
            Explore More
          </h2>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {loading ? (
              <>
                <ProductCardSkeleton />
                <ProductCardSkeleton />
              </>
            ) : (
              availableProducts.map((item) => (
                <ProductCard key={item.product.productId} item={item} />
              ))
            )}
          </div>
        </section>
      )}

      {/* Empty state */}
      {!loading && products.length === 0 && !error && (
        <div className="text-center py-12">
          <Layers className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-lg font-medium mb-2">No products available</h3>
          <p className="text-muted-foreground">
            Products will appear here once they are available.
          </p>
        </div>
      )}
    </div>
  )
}
