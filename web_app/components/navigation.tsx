"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import {
  BarChart3,
  Calendar,
  Menu,
  Trophy,
  TrendingUp,
  X,
} from "lucide-react";
import { ThemeToggle } from "@/src/components/theme-toggle";

const linkBaseClassName =
  "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium " +
  "text-muted-foreground hover:bg-muted hover:text-card-foreground";

export function Navigation() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const links = useMemo(
    () => [
      { href: "/week/14", label: "Weekly", Icon: Calendar },
      { href: "/bowls", label: "Bowls", Icon: Trophy },
      { href: "/models", label: "Models", Icon: BarChart3 },
      { href: "/analytics", label: "Analytics", Icon: TrendingUp },
    ],
    []
  );

  useEffect(() => {
    // Close the mobile menu on navigation.
    setMobileOpen(false);
  }, [pathname]);

  return (
    <nav className="bg-card border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center space-x-2">
            <span className="text-xl font-bold text-card-foreground">
              🏈 Script Ohio 2.0
            </span>
          </Link>

          {/* Desktop */}
          <div className="hidden md:flex items-center gap-2">
            {links.map(({ href, label, Icon }) => (
              <Link
                key={href}
                href={href}
                className={
                  linkBaseClassName +
                  (pathname === href ? " bg-muted text-card-foreground" : "")
                }
              >
                <Icon className="h-4 w-4" />
                <span>{label}</span>
              </Link>
            ))}
            <div className="pl-2">
              <ThemeToggle />
            </div>
          </div>

          {/* Mobile */}
          <div className="flex md:hidden items-center gap-2">
            <ThemeToggle />
            <button
              type="button"
              onClick={() => setMobileOpen((o) => !o)}
              className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-border bg-card text-card-foreground hover:bg-muted focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              aria-label={mobileOpen ? "Close menu" : "Open menu"}
            >
              {mobileOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
            </button>
          </div>
        </div>
      </div>

      {mobileOpen ? (
        <div className="md:hidden border-t border-border bg-card">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex flex-col gap-1">
            {links.map(({ href, label, Icon }) => (
              <Link
                key={href}
                href={href}
                className={
                  linkBaseClassName +
                  (pathname === href ? " bg-muted text-card-foreground" : "")
                }
              >
                <Icon className="h-4 w-4" />
                <span>{label}</span>
              </Link>
            ))}
          </div>
        </div>
      ) : null}
    </nav>
  );
}
