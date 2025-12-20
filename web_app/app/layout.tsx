import type { Metadata } from "next";
import { Navigation } from "@/components/navigation";
import { ThemeProvider } from "@/src/contexts/theme-context";
import "./globals.css";

export const metadata: Metadata = {
  title: "Script Ohio 2.0 Analytics",
  description: "College Football Prediction Platform",
};

const themeInitScript = `(function(){try{var k='so2_theme';var t=localStorage.getItem(k);var m=window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches;var theme=(t==='light'||t==='dark')?t:(m?'dark':'light');if(theme==='dark'){document.documentElement.classList.add('dark');}else{document.documentElement.classList.remove('dark');}}catch(e){}})();`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body className="min-h-screen bg-background text-foreground antialiased transition-colors">
        <ThemeProvider>
          <Navigation />
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
