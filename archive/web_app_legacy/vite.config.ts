import path from "path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"
import { configDefaults } from "vitest/config"

// https://vite.dev/config/
export default defineConfig({
    plugins: [react(), tailwindcss()],
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./src"),
        },
    },
    test: {
        globals: true,
        environment: "jsdom",
        include: ["src/__tests__/**/*.test.ts", "src/**/*.test.ts", "src/**/*.test.tsx"],
        exclude: [...configDefaults.exclude, "dist/**"],
        setupFiles: ["./src/test-utils.tsx"],
        coverage: {
            provider: "istanbul",
            reporter: ["text", "json", "html"],
            reportsDirectory: "coverage",
            include: ["src/**/*.{ts,tsx}"],
            exclude: ["src/**/*.test.{ts,tsx}", "src/test-utils.tsx", "src/main.tsx"],
        },
    },
})
