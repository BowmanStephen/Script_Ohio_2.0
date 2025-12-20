"use client";

import Link from "next/link";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-lg rounded-lg border border-border bg-card p-6 text-card-foreground shadow-sm">
        <h2 className="text-2xl font-bold">Something went wrong</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Please try again. If the issue persists, return to the home page.
        </p>

        <div className="mt-6 flex flex-wrap gap-3">
          <button
            onClick={reset}
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
          >
            Try again
          </button>
          <Link
            href="/"
            className="inline-flex items-center justify-center rounded-md border border-border bg-card px-4 py-2 text-sm font-medium text-card-foreground hover:bg-muted"
          >
            Go home
          </Link>
        </div>

        <details className="mt-6 rounded-md border border-border bg-muted p-3">
          <summary className="cursor-pointer text-sm font-medium text-card-foreground">
            Technical details
          </summary>
          <pre className="mt-3 overflow-x-auto text-xs text-muted-foreground">
            {error.digest ? `digest: ${error.digest}\n` : ""}
            {error.message}
          </pre>
        </details>
      </div>
    </div>
  );
}
