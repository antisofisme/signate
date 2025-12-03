/**
 * Card Component
 *
 * Unified card wrapper with consistent styling across the application
 *
 * Features:
 * - Multiple variants (default, elevated, outlined)
 * - Padding size options
 * - Optional hover effect
 * - Dark mode support
 * - Flexible content layout
 *
 * @usage
 * <Card variant="default" padding="md" hover>
 *   <Card.Header>Title</Card.Header>
 *   <Card.Body>Content</Card.Body>
 *   <Card.Footer>Actions</Card.Footer>
 * </Card>
 */

import { memo, ReactNode, HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils/cn';

type CardVariant = 'default' | 'elevated' | 'outlined';
type CardPadding = 'none' | 'sm' | 'md' | 'lg';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** Visual style variant */
  variant?: CardVariant;
  /** Padding size */
  padding?: CardPadding;
  /** Enable hover effect */
  hover?: boolean;
  /** Make the card clickable with cursor pointer */
  clickable?: boolean;
  /** Additional className */
  className?: string;
  /** Card content */
  children: ReactNode;
}

// Variant styles
const VARIANT_STYLES: Record<CardVariant, string> = {
  default: 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700',
  elevated: 'bg-white dark:bg-gray-800 shadow-md dark:shadow-gray-900/20',
  outlined: 'bg-transparent border-2 border-gray-200 dark:border-gray-700',
};

// Padding styles
const PADDING_STYLES: Record<CardPadding, string> = {
  none: '',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
};

// Hover styles
const HOVER_STYLES = 'hover:shadow-lg dark:hover:shadow-gray-900/30 transition-shadow duration-200';

// Clickable styles
const CLICKABLE_STYLES = 'cursor-pointer';

/**
 * Main Card Component
 */
const Card = memo(forwardRef<HTMLDivElement, CardProps>(function Card(
  {
    variant = 'default',
    padding = 'md',
    hover = false,
    clickable = false,
    className = '',
    children,
    ...props
  },
  ref
) {
  return (
    <div
      ref={ref}
      className={cn(
        'rounded-lg',
        VARIANT_STYLES[variant],
        PADDING_STYLES[padding],
        hover && HOVER_STYLES,
        clickable && CLICKABLE_STYLES,
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}));

/**
 * Card Header Component
 */
interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {
  /** Additional className */
  className?: string;
  children: ReactNode;
}

const CardHeader = memo<CardHeaderProps>(function CardHeader({
  className = '',
  children,
  ...props
}) {
  return (
    <div
      className={cn(
        'border-b border-gray-200 dark:border-gray-700 pb-4 mb-4',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
});

/**
 * Card Body Component
 */
interface CardBodyProps extends HTMLAttributes<HTMLDivElement> {
  /** Additional className */
  className?: string;
  children: ReactNode;
}

const CardBody = memo<CardBodyProps>(function CardBody({
  className = '',
  children,
  ...props
}) {
  return (
    <div className={cn('', className)} {...props}>
      {children}
    </div>
  );
});

/**
 * Card Footer Component
 */
interface CardFooterProps extends HTMLAttributes<HTMLDivElement> {
  /** Additional className */
  className?: string;
  children: ReactNode;
}

const CardFooter = memo<CardFooterProps>(function CardFooter({
  className = '',
  children,
  ...props
}) {
  return (
    <div
      className={cn(
        'border-t border-gray-200 dark:border-gray-700 pt-4 mt-4',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
});

/**
 * Card Title Component
 */
interface CardTitleProps extends HTMLAttributes<HTMLHeadingElement> {
  /** Additional className */
  className?: string;
  children: ReactNode;
}

const CardTitle = memo<CardTitleProps>(function CardTitle({
  className = '',
  children,
  ...props
}) {
  return (
    <h3
      className={cn(
        'text-lg font-semibold text-gray-900 dark:text-white',
        className
      )}
      {...props}
    >
      {children}
    </h3>
  );
});

/**
 * Card Description Component
 */
interface CardDescriptionProps extends HTMLAttributes<HTMLParagraphElement> {
  /** Additional className */
  className?: string;
  children: ReactNode;
}

const CardDescription = memo<CardDescriptionProps>(function CardDescription({
  className = '',
  children,
  ...props
}) {
  return (
    <p
      className={cn(
        'text-sm text-gray-500 dark:text-gray-400 mt-1',
        className
      )}
      {...props}
    >
      {children}
    </p>
  );
});

// Compound components
const CardCompound = Object.assign(Card, {
  Header: CardHeader,
  Body: CardBody,
  Footer: CardFooter,
  Title: CardTitle,
  Description: CardDescription,
});

export default CardCompound;
export {
  Card,
  CardHeader,
  CardBody,
  CardFooter,
  CardTitle,
  CardDescription,
};
export type {
  CardProps,
  CardHeaderProps,
  CardBodyProps,
  CardFooterProps,
  CardTitleProps,
  CardDescriptionProps,
  CardVariant,
  CardPadding,
};
