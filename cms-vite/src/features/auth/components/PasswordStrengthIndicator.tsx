/**
 * Password Strength Indicator Component
 * Visual indicator untuk menampilkan kekuatan password
 */

interface PasswordStrength {
  score: number; // 0-4
  label: string;
  color: string;
  requirements: {
    minLength: boolean;
    hasUppercase: boolean;
    hasLowercase: boolean;
    hasNumber: boolean;
  };
}

interface PasswordStrengthIndicatorProps {
  password: string;
  showRequirements?: boolean;
}

/**
 * Calculate password strength
 */
const calculateStrength = (password: string): PasswordStrength => {
  const requirements = {
    minLength: password.length >= 8,
    hasUppercase: /[A-Z]/.test(password),
    hasLowercase: /[a-z]/.test(password),
    hasNumber: /\d/.test(password),
  };

  // Count fulfilled requirements
  const fulfilledCount = Object.values(requirements).filter(Boolean).length;

  // Calculate score (0-4)
  let score = 0;
  if (password.length > 0) {
    score = fulfilledCount;
  }

  // Determine label and color
  const getStrengthInfo = (score: number) => {
    if (score === 0) return { label: 'Terlalu Lemah', color: 'text-gray-400' };
    if (score === 1) return { label: 'Lemah', color: 'text-red-600' };
    if (score === 2) return { label: 'Sedang', color: 'text-orange-500' };
    if (score === 3) return { label: 'Kuat', color: 'text-yellow-500' };
    return { label: 'Sangat Kuat', color: 'text-green-600' };
  };

  const { label, color } = getStrengthInfo(score);

  return {
    score,
    label,
    color,
    requirements,
  };
};

/**
 * Get bar color based on score
 */
const getBarColor = (index: number, score: number): string => {
  if (index >= score) return 'bg-gray-200';
  if (score === 1) return 'bg-red-500';
  if (score === 2) return 'bg-orange-500';
  if (score === 3) return 'bg-yellow-500';
  return 'bg-green-500';
};

export function PasswordStrengthIndicator({
  password,
  showRequirements = true,
}: PasswordStrengthIndicatorProps) {
  const strength = calculateStrength(password);

  if (!password) return null;

  return (
    <div className="mt-2">
      {/* Strength Bars */}
      <div className="flex gap-1 mb-2">
        {[0, 1, 2, 3].map((index) => (
          <div
            key={index}
            className={`h-1 flex-1 rounded transition-colors duration-300 ${getBarColor(
              index,
              strength.score
            )}`}
          />
        ))}
      </div>

      {/* Strength Label */}
      <p className={`text-sm font-medium ${strength.color}`}>
        Kekuatan: {strength.label}
      </p>

      {/* Requirements Checklist */}
      {showRequirements && (
        <ul className="mt-2 space-y-1 text-xs">
          <li
            className={`flex items-center gap-1 ${
              strength.requirements.minLength ? 'text-green-600' : 'text-gray-500'
            }`}
          >
            {strength.requirements.minLength ? (
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            )}
            Minimal 8 karakter
          </li>
          <li
            className={`flex items-center gap-1 ${
              strength.requirements.hasUppercase ? 'text-green-600' : 'text-gray-500'
            }`}
          >
            {strength.requirements.hasUppercase ? (
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            )}
            Huruf besar (A-Z)
          </li>
          <li
            className={`flex items-center gap-1 ${
              strength.requirements.hasLowercase ? 'text-green-600' : 'text-gray-500'
            }`}
          >
            {strength.requirements.hasLowercase ? (
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            )}
            Huruf kecil (a-z)
          </li>
          <li
            className={`flex items-center gap-1 ${
              strength.requirements.hasNumber ? 'text-green-600' : 'text-gray-500'
            }`}
          >
            {strength.requirements.hasNumber ? (
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            )}
            Angka (0-9)
          </li>
        </ul>
      )}
    </div>
  );
}
