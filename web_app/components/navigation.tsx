import Link from "next/link";
import { Calendar, Trophy, BarChart3, TrendingUp } from "lucide-react";
import { ThemeToggle } from "@/src/components/theme-toggle";

const linkBaseClassName =
  "flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium " +
  "text-muted-foreground hover:bg-muted hover:text-card-foreground";

export function Navigation() {
  return (
    <nav className="bg-card border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center space-x-2">
            <span className="text-xl font-bold text-card-foreground">
              🏈 Script Ohio 2.0
            </span>
          </Link>

          <div className="flex items-center space-x-2">
            <Link href="/week/14" className={linkBaseClassName}>
              <Calendar className="h-4 w-4" />
              <span>Weekly</span>
            </Link>
            <Link href="/bowls" className={linkBaseClassName}>
              <Trophy className="h-4 w-4" />
              <span>Bowls</span>
            </Link>
            <Link href="/models" className={linkBaseClassName}>
              <BarChart3 className="h-4 w-4" />
              <span>Models</span>
            </Link>
            <Link href="/analytics" className={linkBaseClassName}>
              <TrendingUp className="h-4 w-4" />
              <span>Analytics</span>
            </Link>

            <div className="pl-2">
              <ThemeToggle />
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
