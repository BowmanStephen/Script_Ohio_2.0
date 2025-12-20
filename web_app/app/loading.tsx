export default function Loading() {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-64 rounded-md bg-muted" />
          <div className="h-4 w-44 rounded-md bg-muted" />
          <div className="h-10 w-full rounded-md bg-muted" />
          <div className="h-80 w-full rounded-md bg-muted" />
        </div>
      </div>
    </div>
  );
}
