import { colors } from './src/styles/tokens.js'

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // Integrate design tokens
      colors: {
        primary: colors.primary,
        success: colors.success,
        warning: colors.warning,
        danger: colors.danger,
        info: colors.info,
        gray: colors.gray,
      },
      // Keep Tailwind defaults for other colors
      // but our custom colors will override them
    },
  },
  plugins: [],
}
