"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

export type Theme = "light" | "dark";

type ThemeContextValue = {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
};

const THEME_STORAGE_KEY = "so2_theme";

const ThemeContext = createContext<ThemeContextValue | null>(null);

function getSystemTheme(): Theme {
  if (typeof window === "undefined") return "light";
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function normalizeTheme(value: unknown): Theme | null {
  if (value === "light" || value === "dark") return value;
  return null;
}

function applyThemeToDocument(theme: Theme) {
  const root = document.documentElement;
  if (theme === "dark") root.classList.add("dark");
  else root.classList.remove("dark");
}

export function ThemeProvider({
  children,
}: {
  children: React.ReactNode;
}): React.ReactNode {
  const [theme, setThemeState] = useState<Theme>("light");
  const [mounted, setMounted] = useState(false);

  // Initialize theme from localStorage (or system) on mount.
  useEffect(() => {
    let initial: Theme = "light";

    try {
      const stored = normalizeTheme(localStorage.getItem(THEME_STORAGE_KEY));
      initial = stored ?? getSystemTheme();
    } catch {
      initial = getSystemTheme();
    }

    setThemeState(initial);
    applyThemeToDocument(initial);
    setMounted(true);
  }, []);

  // Persist + apply on changes.
  useEffect(() => {
    if (!mounted) return;

    try {
      localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch {
      // ignore
    }

    applyThemeToDocument(theme);
  }, [mounted, theme]);

  const setTheme = useCallback((next: Theme) => {
    setThemeState(next);
  }, []);

  const toggleTheme = useCallback(() => {
    setThemeState((prev) => (prev === "dark" ? "light" : "dark"));
  }, []);

  const value = useMemo(
    () => ({
      theme,
      setTheme,
      toggleTheme,
    }),
    [theme, setTheme, toggleTheme]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return ctx;
}

export const themeInitScript = `(function(){try{var k='${THEME_STORAGE_KEY}';var t=localStorage.getItem(k);var m=window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches;var theme=(t==='light'||t==='dark')?t:(m?'dark':'light');if(theme==='dark'){document.documentElement.classList.add('dark');}else{document.documentElement.classList.remove('dark');}}catch(e){}})();`;
