/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: '#0f274d',
        slateblue: '#4f658a',
        paper: '#f8f7f4',
        mist: '#edf3fb',
        bubble: '#d9e8f8'
      },
      boxShadow: {
        book: '0 18px 40px -18px rgba(15, 39, 77, 0.35)',
        panel: '0 10px 24px -16px rgba(15, 39, 77, 0.3)'
      }
    }
  },
  plugins: []
};
