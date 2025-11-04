/**
 * Error Messages
 * Centralized error message mapping
 */

import { ErrorCodes } from './apiErrors';

export const errorMessages: Record<string, string> = {
  // Authentication & Authorization
  [ErrorCodes.INVALID_CREDENTIALS]: 'Username atau password salah',
  [ErrorCodes.TOKEN_EXPIRED]: 'Sesi Anda telah berakhir, silakan login kembali',
  [ErrorCodes.TOKEN_INVALID]: 'Token tidak valid',
  [ErrorCodes.ACCESS_DENIED]: 'Anda tidak memiliki akses ke resource ini',

  // Validation
  [ErrorCodes.INVALID_INPUT]: 'Input tidak valid',
  [ErrorCodes.MISSING_FIELD]: 'Field wajib tidak boleh kosong',
  [ErrorCodes.INVALID_FORMAT]: 'Format input tidak valid',

  // Resources
  [ErrorCodes.NOT_FOUND]: 'Resource tidak ditemukan',
  [ErrorCodes.ALREADY_EXISTS]: 'Resource sudah ada',

  // Business Logic
  [ErrorCodes.ACTIVATION_CODE_EXPIRED]: 'Kode aktivasi sudah kadaluarsa',
  [ErrorCodes.ACTIVATION_CODE_INVALID]: 'Kode aktivasi tidak valid',
  [ErrorCodes.DEVICE_ALREADY_ACTIVATED]: 'Device sudah diaktivasi',

  // System
  [ErrorCodes.NETWORK_ERROR]: 'Terjadi kesalahan jaringan',
  [ErrorCodes.INTERNAL_ERROR]: 'Terjadi kesalahan sistem',
};

export function getErrorMessage(code: string, fallback?: string): string {
  return errorMessages[code] || fallback || 'Terjadi kesalahan yang tidak diketahui';
}
