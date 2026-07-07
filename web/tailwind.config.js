/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        vintage: {
          cream: '#f5e6d3',
          parchment: '#efe0d0',
          ink: '#3b2208',
          brown: '#8b4513',
          darkbrown: '#5c2e0a',
          accent: '#c94c4c',
          forest: '#2e4a3f',
          amber: '#d4a373',
          gold: '#816904',
          wheat: '#eedbc2',
        },
      },
      fontFamily: {
        serif: ['Georgia', 'Times New Roman', 'Baskerville', 'Palatino', 'serif'],
        heading: ['Georgia', 'Times New Roman', 'Baskerville', 'serif'],
      },
      borderRadius: {
        none: '0px',
        sm: '2px',
      },
      borderWidth: {
        '3': '3px',
      },
      boxShadow: {
        'vintage-sm': '0 2px 4px rgba(139,69,19,0.1)',
        'vintage-md': '0 4px 8px rgba(139,69,19,0.15)',
        'vintage-lg': '0 8px 16px rgba(139,69,19,0.2)',
        'vintage-hover': '0 4px 12px rgba(139,69,19,0.2)',
      },
      transitionDuration: {
        '700': '700ms',
      },
    },
  },
  plugins: [],
}