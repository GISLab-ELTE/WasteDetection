import { resolve } from "path";

const BASE_URL = process.env.VITE_BASE_URL || "";

export default {
  base: BASE_URL,
  build: {
    sourcemap: true,
    target: "esnext",
    rollupOptions: {
      input: {
        main: resolve(__dirname, "index.html"),
        demo: resolve(__dirname, "demo.html"),
        login: resolve(__dirname, "login.html"),
      },
    },
  },
};
