/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        archive: {
          bg: '#0a0a0c',
          surface: '#111114',
          border: '#2a2a2e',
          text: '#e5e5e5',
          muted: '#6b6b70',
          red: '#ef4444',   // Proletariat
          blue: '#3b82f6',  // Bourgeoisie
          gold: '#eab308',  // Events
          green: '#22c55e'  // Concepts
        }
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
        sans: ['"Inter"', 'ui-sans-serif', 'system-ui']
      },
      backgroundImage: {
        'grid-archival': 'linear-gradient(to right, #1a1a1e 1px, transparent 1px), linear-gradient(to bottom, #1a1a1e 1px, transparent 1px)'
      }
    }
  },
  plugins: [],
}
