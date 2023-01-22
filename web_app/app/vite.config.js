const BASE_URL = process.env.VITE_BASE_URL || '';

export default {
  base: BASE_URL,
  build: {
    sourcemap: true,
    target: 'esnext',
  }
}
