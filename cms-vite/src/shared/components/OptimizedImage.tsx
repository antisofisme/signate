/**
 * Optimized Image Component
 *
 * Provides lazy loading, error handling, and loading states for images.
 *
 * Features:
 * - Lazy loading with IntersectionObserver
 * - Loading skeleton placeholder
 * - Error fallback UI
 * - Responsive sizing support
 * - Accessibility attributes
 *
 * @usage
 * <OptimizedImage
 *   src="/path/to/image.jpg"
 *   alt="Description"
 *   className="w-full rounded-lg"
 * />
 */

import { useState, useRef, useEffect, ImgHTMLAttributes } from 'react';
import { ImageOff } from 'lucide-react';

// ============================================================================
// TYPES
// ============================================================================

interface OptimizedImageProps extends Omit<ImgHTMLAttributes<HTMLImageElement>, 'onError' | 'onLoad'> {
  /** Image source URL */
  src: string;
  /** Alt text for accessibility */
  alt: string;
  /** Fallback element when image fails to load */
  fallback?: React.ReactNode;
  /** Show loading skeleton */
  showSkeleton?: boolean;
  /** Custom skeleton className */
  skeletonClassName?: string;
  /** Disable lazy loading */
  eager?: boolean;
  /** Callback when image loads successfully */
  onLoadSuccess?: () => void;
  /** Callback when image fails to load */
  onLoadError?: (error: Event) => void;
  /** Aspect ratio for skeleton (e.g., "16/9", "1/1", "4/3") */
  aspectRatio?: string;
}

// ============================================================================
// LOADING SKELETON
// ============================================================================

interface SkeletonProps {
  className?: string;
  aspectRatio?: string;
}

function ImageSkeleton({ className = '', aspectRatio }: SkeletonProps) {
  const aspectStyle = aspectRatio ? { aspectRatio } : {};

  return (
    <div
      className={`bg-gray-200 dark:bg-gray-700 animate-pulse flex items-center justify-center ${className}`}
      style={aspectStyle}
      role="presentation"
      aria-hidden="true"
    >
      <svg
        className="w-8 h-8 text-gray-300 dark:text-gray-600"
        xmlns="http://www.w3.org/2000/svg"
        fill="currentColor"
        viewBox="0 0 20 18"
        aria-hidden="true"
      >
        <path d="M18 0H2a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2Zm-5.5 4a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3Zm4.376 10.481A1 1 0 0 1 16 15H4a1 1 0 0 1-.895-1.447l3.5-7A1 1 0 0 1 7.468 6a.965.965 0 0 1 .9.5l2.775 4.757 1.546-1.887a1 1 0 0 1 1.618.1l2.541 4a1 1 0 0 1 .028 1.011Z" />
      </svg>
    </div>
  );
}

// ============================================================================
// ERROR FALLBACK
// ============================================================================

interface ErrorFallbackProps {
  className?: string;
  aspectRatio?: string;
}

function DefaultErrorFallback({ className = '', aspectRatio }: ErrorFallbackProps) {
  const aspectStyle = aspectRatio ? { aspectRatio } : {};

  return (
    <div
      className={`bg-gray-100 dark:bg-gray-800 flex items-center justify-center ${className}`}
      style={aspectStyle}
      role="img"
      aria-label="Image failed to load"
    >
      <div className="text-center text-gray-400 dark:text-gray-500">
        <ImageOff className="w-8 h-8 mx-auto mb-1" aria-hidden="true" />
        <span className="text-xs">Failed to load</span>
      </div>
    </div>
  );
}

// ============================================================================
// OPTIMIZED IMAGE COMPONENT
// ============================================================================

export function OptimizedImage({
  src,
  alt,
  className = '',
  fallback,
  showSkeleton = true,
  skeletonClassName,
  eager = false,
  onLoadSuccess,
  onLoadError,
  aspectRatio,
  ...imgProps
}: OptimizedImageProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [isInView, setIsInView] = useState(eager);
  const imgRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Lazy loading with IntersectionObserver
  useEffect(() => {
    if (eager || !containerRef.current) {
      setIsInView(true);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsInView(true);
            observer.disconnect();
          }
        });
      },
      {
        rootMargin: '50px', // Start loading 50px before entering viewport
        threshold: 0,
      }
    );

    observer.observe(containerRef.current);

    return () => {
      observer.disconnect();
    };
  }, [eager]);

  // Reset state when src changes
  useEffect(() => {
    setIsLoading(true);
    setHasError(false);
  }, [src]);

  const handleLoad = () => {
    setIsLoading(false);
    setHasError(false);
    onLoadSuccess?.();
  };

  const handleError = (event: React.SyntheticEvent<HTMLImageElement, Event>) => {
    setIsLoading(false);
    setHasError(true);
    onLoadError?.(event.nativeEvent);
  };

  // Error state
  if (hasError) {
    return (
      <div ref={containerRef} className={className}>
        {fallback || <DefaultErrorFallback className={className} aspectRatio={aspectRatio} />}
      </div>
    );
  }

  return (
    <div ref={containerRef} className="relative">
      {/* Loading skeleton */}
      {showSkeleton && isLoading && (
        <ImageSkeleton
          className={skeletonClassName || className}
          aspectRatio={aspectRatio}
        />
      )}

      {/* Actual image */}
      {isInView && (
        <img
          ref={imgRef}
          src={src}
          alt={alt}
          className={`${className} ${isLoading ? 'invisible absolute inset-0' : ''}`}
          onLoad={handleLoad}
          onError={handleError}
          loading={eager ? 'eager' : 'lazy'}
          decoding="async"
          {...imgProps}
        />
      )}
    </div>
  );
}

// ============================================================================
// THUMBNAIL IMAGE (Preset for small images)
// ============================================================================

interface ThumbnailProps extends Omit<OptimizedImageProps, 'showSkeleton' | 'aspectRatio'> {
  /** Thumbnail size in pixels */
  size?: number;
}

export function Thumbnail({
  size = 40,
  className = '',
  ...props
}: ThumbnailProps) {
  return (
    <OptimizedImage
      className={`object-cover rounded ${className}`}
      style={{ width: size, height: size }}
      aspectRatio="1/1"
      {...props}
    />
  );
}

// ============================================================================
// AVATAR IMAGE (Preset for user avatars)
// ============================================================================

interface AvatarProps extends Omit<OptimizedImageProps, 'showSkeleton' | 'aspectRatio' | 'fallback'> {
  /** Avatar size: 'sm' | 'md' | 'lg' | 'xl' */
  size?: 'sm' | 'md' | 'lg' | 'xl';
  /** Fallback initials when image fails */
  initials?: string;
}

const AVATAR_SIZES = {
  sm: 'w-8 h-8 text-xs',
  md: 'w-10 h-10 text-sm',
  lg: 'w-12 h-12 text-base',
  xl: 'w-16 h-16 text-lg',
} as const;

export function Avatar({
  size = 'md',
  initials,
  className = '',
  ...props
}: AvatarProps) {
  const sizeClass = AVATAR_SIZES[size];

  const fallbackElement = initials ? (
    <div
      className={`${sizeClass} rounded-full bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 flex items-center justify-center font-medium ${className}`}
      role="img"
      aria-label={props.alt}
    >
      {initials.slice(0, 2).toUpperCase()}
    </div>
  ) : undefined;

  return (
    <OptimizedImage
      className={`${sizeClass} rounded-full object-cover ${className}`}
      aspectRatio="1/1"
      fallback={fallbackElement}
      {...props}
    />
  );
}

// ============================================================================
// EXPORTS
// ============================================================================

export type { OptimizedImageProps, ThumbnailProps, AvatarProps };
