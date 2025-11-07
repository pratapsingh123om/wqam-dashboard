// Try new @tailwindcss/postcss plugin, fall back to classic tailwindcss if not installed.
let tailwindPlugin;
try {
  tailwindPlugin = require('@tailwindcss/postcss');
} catch (e) {
  try {
    tailwindPlugin = require('tailwindcss');
  } catch (e2) {
    // If require fails in some environments, let PostCSS resolve by name.
    tailwindPlugin = 'tailwindcss';
  }
}

module.exports = {
  plugins: [
    tailwindPlugin,
    require('autoprefixer'),
  ],
};
