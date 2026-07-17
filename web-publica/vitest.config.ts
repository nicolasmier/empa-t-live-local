import { defineConfig } from "vitest/config";

// Config separada de vite.config.ts a propósito: mezclar el plugin de React
// del proyecto con el `defineConfig` de vitest/config choca a nivel de tipos
// (dos resoluciones de `vite` distintas). Los tests actuales son lógica pura
// sin JSX, así que no hace falta el plugin aquí.
export default defineConfig({
  test: {
    environment: "jsdom",
  },
});
