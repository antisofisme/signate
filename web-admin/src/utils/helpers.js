/**
 * Helper Utilities
 * General purpose helper functions
 */

/**
 * Generate cryptographically secure random ID
 * Uses Web Crypto API for security-safe random UUID generation
 * @returns {string} Random UUID (e.g., "123e4567-e89b-12d3-a456-426614174000")
 */
export function generateId() {
  return crypto.randomUUID()
}

/**
 * Debounce function
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
export function debounce(func, wait = 300) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

/**
 * Sleep/delay function
 * @param {number} ms - Milliseconds to sleep
 * @returns {Promise} Promise that resolves after delay
 */
export function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * Check if object is empty
 * @param {Object} obj - Object to check
 * @returns {boolean} True if empty
 */
export function isEmpty(obj) {
  return Object.keys(obj).length === 0
}

/**
 * Deep clone object
 * @param {*} obj - Object to clone
 * @returns {*} Cloned object
 */
export function deepClone(obj) {
  return JSON.parse(JSON.stringify(obj))
}

/**
 * Remove duplicates from array
 * @param {Array} array - Array with possible duplicates
 * @returns {Array} Array without duplicates
 */
export function removeDuplicates(array) {
  return [...new Set(array)]
}

/**
 * Group array by key
 * @param {Array} array - Array to group
 * @param {string} key - Key to group by
 * @returns {Object} Grouped object
 */
export function groupBy(array, key) {
  return array.reduce((result, item) => {
    const group = item[key]
    if (!result[group]) {
      result[group] = []
    }
    result[group].push(item)
    return result
  }, {})
}

/**
 * Sort array by key
 * @param {Array} array - Array to sort
 * @param {string} key - Key to sort by
 * @param {string} order - 'asc' or 'desc'
 * @returns {Array} Sorted array
 */
export function sortBy(array, key, order = 'asc') {
  return [...array].sort((a, b) => {
    const aVal = a[key]
    const bVal = b[key]

    if (aVal < bVal) return order === 'asc' ? -1 : 1
    if (aVal > bVal) return order === 'asc' ? 1 : -1
    return 0
  })
}

/**
 * Filter array by search text (multiple fields)
 * @param {Array} array - Array to filter
 * @param {string} searchText - Text to search
 * @param {Array} fields - Fields to search in
 * @returns {Array} Filtered array
 */
export function filterBySearch(array, searchText, fields) {
  if (!searchText) return array

  const lowercaseSearch = searchText.toLowerCase()

  return array.filter(item => {
    return fields.some(field => {
      const value = item[field]
      if (!value) return false
      return String(value).toLowerCase().includes(lowercaseSearch)
    })
  })
}

/**
 * Download file
 * @param {Blob|string} data - File data or URL
 * @param {string} filename - Filename
 */
export function downloadFile(data, filename) {
  const url = data instanceof Blob ? URL.createObjectURL(data) : data
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  if (data instanceof Blob) {
    URL.revokeObjectURL(url)
  }
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise<boolean>} Success status
 */
export async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch (error) {
    console.error('Failed to copy:', error)
    return false
  }
}

/**
 * Check if device is mobile
 * @returns {boolean} True if mobile
 */
export function isMobile() {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
    navigator.userAgent
  )
}

/**
 * Get file extension from filename
 * @param {string} filename - Filename
 * @returns {string} File extension
 */
export function getFileExtension(filename) {
  return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2)
}

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean} True if valid
 */
export function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * Validate URL format
 * @param {string} url - URL to validate
 * @returns {boolean} True if valid
 */
export function isValidUrl(url) {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

/**
 * Validate IPv4 address format
 * @param {string} ip - IP address to validate
 * @returns {boolean} True if valid IPv4 address
 */
export function isValidIPv4(ip) {
  // Regex pattern for IPv4 validation
  const ipv4Regex = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/

  if (!ipv4Regex.test(ip)) {
    return false
  }

  // Validate each octet is between 0-255
  const octets = ip.split('.')
  return octets.every(octet => {
    const num = parseInt(octet, 10)
    return num >= 0 && num <= 255
  })
}

/**
 * Validate password strength
 * @param {string} password - Password to validate
 * @returns {Object} Validation result with isValid flag and strength level
 */
export function validatePasswordStrength(password) {
  const result = {
    isValid: false,
    strength: 'weak',
    issues: []
  }

  // Minimum length requirement
  if (password.length < 8) {
    result.issues.push('Must be at least 8 characters long')
  }

  // Uppercase letter requirement
  if (!/[A-Z]/.test(password)) {
    result.issues.push('Must contain at least one uppercase letter')
  }

  // Lowercase letter requirement
  if (!/[a-z]/.test(password)) {
    result.issues.push('Must contain at least one lowercase letter')
  }

  // Number requirement
  if (!/\d/.test(password)) {
    result.issues.push('Must contain at least one number')
  }

  // Determine strength based on criteria met
  const criteriaMet = 4 - result.issues.length

  if (criteriaMet === 4) {
    result.strength = 'strong'
    result.isValid = true
  } else if (criteriaMet === 3) {
    result.strength = 'medium'
    result.isValid = false
  } else {
    result.strength = 'weak'
    result.isValid = false
  }

  return result
}

/**
 * File validation configuration
 */
const FILE_VALIDATION_CONFIG = {
  maxSize: {
    image: 5 * 1024 * 1024,    // 5MB for images
    video: 100 * 1024 * 1024   // 100MB for videos
  },
  allowedMimeTypes: {
    image: ['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'image/gif', 'image/bmp', 'image/svg+xml'],
    video: ['video/mp4', 'video/webm', 'video/ogg']
  },
  // Magic numbers (file signatures) for common formats
  magicNumbers: {
    'image/png': [[0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]],
    'image/jpeg': [[0xFF, 0xD8, 0xFF]],
    'image/jpg': [[0xFF, 0xD8, 0xFF]],
    'image/gif': [[0x47, 0x49, 0x46, 0x38]],
    'image/webp': [[0x52, 0x49, 0x46, 0x46]], // RIFF (first 4 bytes)
    'image/bmp': [[0x42, 0x4D]],
    'video/mp4': [[0x00, 0x00, 0x00], [0x66, 0x74, 0x79, 0x70]], // ftyp at offset 4
    'video/webm': [[0x1A, 0x45, 0xDF, 0xA3]],
    'video/ogg': [[0x4F, 0x67, 0x67, 0x53]]
  }
}

/**
 * Read file header bytes for magic number validation
 * @param {File} file - File object to read
 * @param {number} bytes - Number of bytes to read (default 12)
 * @returns {Promise<Uint8Array>} First N bytes of the file
 */
async function readFileHeader(file, bytes = 12) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    const blob = file.slice(0, bytes)

    reader.onload = (e) => resolve(new Uint8Array(e.target.result))
    reader.onerror = (e) => reject(e)

    reader.readAsArrayBuffer(blob)
  })
}

/**
 * Check if file header matches expected magic numbers
 * @param {Uint8Array} header - File header bytes
 * @param {Array} magicNumbers - Array of magic number patterns
 * @returns {boolean} True if header matches any pattern
 */
function matchesMagicNumber(header, magicNumbers) {
  return magicNumbers.some(pattern => {
    return pattern.every((byte, index) => header[index] === byte)
  })
}

/**
 * Validate file upload
 * @param {File} file - File object to validate
 * @param {Object} options - Validation options
 * @returns {Promise<Object>} Validation result with isValid flag and error messages
 */
export async function validateFileUpload(file, options = {}) {
  const result = {
    isValid: true,
    errors: []
  }

  // Determine file category
  const isImage = file.type.startsWith('image/')
  const isVideo = file.type.startsWith('video/')

  if (!isImage && !isVideo) {
    result.isValid = false
    result.errors.push('File must be an image or video')
    return result
  }

  const category = isImage ? 'image' : 'video'
  const maxSize = options.maxSize || FILE_VALIDATION_CONFIG.maxSize[category]
  const allowedMimeTypes = options.allowedMimeTypes || FILE_VALIDATION_CONFIG.allowedMimeTypes[category]

  // 1. File size validation
  if (file.size > maxSize) {
    result.isValid = false
    result.errors.push(
      `File size exceeds ${(maxSize / 1024 / 1024).toFixed(0)}MB limit (current: ${(file.size / 1024 / 1024).toFixed(2)}MB)`
    )
  }

  // 2. MIME type validation
  if (!allowedMimeTypes.includes(file.type)) {
    result.isValid = false
    result.errors.push(`File type '${file.type}' is not allowed`)
  }

  // 3. Magic number validation (file signature)
  try {
    const header = await readFileHeader(file)
    const magicPatterns = FILE_VALIDATION_CONFIG.magicNumbers[file.type]

    if (magicPatterns && !matchesMagicNumber(header, magicPatterns)) {
      result.isValid = false
      result.errors.push(
        `File signature doesn't match ${file.type}. File may be corrupted or have wrong extension.`
      )
    }
  } catch (error) {
    result.isValid = false
    result.errors.push('Failed to read file signature')
  }

  return result
}

/**
 * Format file size to human-readable string
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size (e.g., "1.5 MB")
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`
}
