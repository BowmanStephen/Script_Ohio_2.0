import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-foreground mb-2">
            🏈 Script Ohio 2.0 Analytics
          </h1>
          <p className="text-lg text-muted-foreground">
            College Football Prediction Platform
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
          <Link
            href="/week/14"
            className="rounded-lg border border-border bg-card p-6 shadow-sm transition-shadow hover:shadow-md"
          >
            <h2 className="text-xl font-semibold mb-2 text-card-foreground">
              Weekly Predictions
            </h2>
            <p className="text-muted-foreground">
              View predictions for current week games
            </p>
          </Link>

          <Link
            href="/bowls"
            className="rounded-lg border border-border bg-card p-6 shadow-sm transition-shadow hover:shadow-md"
          >
            <h2 className="text-xl font-semibold mb-2 text-card-foreground">
              Bowl Season
            </h2>
            <p className="text-muted-foreground">Bowl and postseason predictions</p>
          </Link>

          <Link
            href="/models"
            className="rounded-lg border border-border bg-card p-6 shadow-sm transition-shadow hover:shadow-md"
          >
            <h2 className="text-xl font-semibold mb-2 text-card-foreground">
              Model Comparison
            </h2>
            <p className="text-muted-foreground">
              Compare Ridge, XGBoost, FastAI, Ensemble
            </p>
          </Link>

          <Link
            href="/analytics"
            className="rounded-lg border border-border bg-card p-6 shadow-sm transition-shadow hover:shadow-md"
          >
            <h2 className="text-xl font-semibold mb-2 text-card-foreground">
              Advanced Analytics
            </h2>
            <p className="text-muted-foreground">Deep dive into model performance</p>
          </Link>
        </div>
      </div>
    </div>
  );
}
