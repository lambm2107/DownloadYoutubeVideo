/**
 * Vite config cho Desktop (Electron) build.
 * Build SPA thuần — không SSR, không TanStack Start.
 * Output ra dist-desktop/ để Electron load file:// trực tiếp.
 */
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import tsconfigPaths from "vite-tsconfig-paths";
import path from "path";

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    tsconfigPaths(),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    outDir: "dist-desktop",
    emptyOutDir: true,
    // Dùng relative paths để file:// protocol hoạt động
    base: "./",
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, "index.desktop.html"),
      },
    },
  },
  // Không cần dev server cho desktop build
});
