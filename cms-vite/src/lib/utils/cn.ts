/**
 * Tailwind CSS Class Name Merger
 *
 * Combines clsx and tailwind-merge for better class composition
 *
 * Usage:
 *   cn("px-2 py-1", "bg-blue-500", { "text-white": isActive })
 */

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
