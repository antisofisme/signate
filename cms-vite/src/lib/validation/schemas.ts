/**
 * Validation Schemas
 * Common validation rules (can use Zod or Yup in future)
 */

export const validators = {
  email: (value: string): boolean => {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(value);
  },

  username: (value: string): { valid: boolean; error?: string } => {
    if (value.length < 3 || value.length > 50) {
      return { valid: false, error: 'Username must be 3-50 characters' };
    }
    if (!/^[a-zA-Z0-9_-]+$/.test(value)) {
      return { valid: false, error: 'Username can only contain letters, numbers, - and _' };
    }
    return { valid: true };
  },

  password: (value: string): { valid: boolean; error?: string } => {
    if (value.length < 8) {
      return { valid: false, error: 'Password must be at least 8 characters' };
    }
    if (!/[A-Z]/.test(value)) {
      return { valid: false, error: 'Password must contain uppercase letter' };
    }
    if (!/[a-z]/.test(value)) {
      return { valid: false, error: 'Password must contain lowercase letter' };
    }
    if (!/\d/.test(value)) {
      return { valid: false, error: 'Password must contain a number' };
    }
    return { valid: true };
  },

  activationCode: (value: string): { valid: boolean; error?: string } => {
    if (value.length !== 6) {
      return { valid: false, error: 'Activation code must be 6 characters' };
    }
    if (!/^[A-Z0-9]+$/.test(value)) {
      return { valid: false, error: 'Activation code must be alphanumeric uppercase' };
    }
    return { valid: true };
  },

  required: (value: any): boolean => {
    if (typeof value === 'string') return value.trim().length > 0;
    return value !== null && value !== undefined;
  },

  minLength: (value: string, min: number): boolean => {
    return value.length >= min;
  },

  maxLength: (value: string, max: number): boolean => {
    return value.length <= max;
  },

  numeric: (value: string): boolean => {
    return /^\d+$/.test(value);
  },

  url: (value: string): boolean => {
    try {
      new URL(value);
      return true;
    } catch {
      return false;
    }
  },
};
