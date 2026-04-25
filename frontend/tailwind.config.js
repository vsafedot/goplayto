/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink:     '#0a0a0a',
        paper:   '#ffffff',
        canvas:  '#f0ede8',
        muted:   '#888888',
        border:  '#0a0a0a',
        success: '#16a34a',
        danger:  '#dc2626',
        warn:    '#d97706',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      boxShadow: {
        'block':    '5px 5px 0 #0a0a0a',
        'block-sm': '3px 3px 0 #0a0a0a',
        'block-lg': '8px 8px 0 #0a0a0a',
      },
      borderRadius: {
        DEFAULT: '0',
      }
    },
  },
  plugins: [],
}
