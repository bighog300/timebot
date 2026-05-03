export function LoadingState({ label = 'Loading...' }: { label?: string }) {
  return <div className="animate-pulse text-sm text-slate-400">{label}</div>;
}

export function EmptyState({ label }: { label: string }) {
  return <div className="rounded border border-dashed border-slate-700 p-8 text-center text-slate-400">{label}</div>;
}

export function ErrorState({ message }: { message: string }) {
  return <div className="rounded border border-red-800 bg-red-950/40 p-4 text-red-300">{message}</div>;
}

/**
 * SkeletonCard — placeholder for a loading card.
 * Use `lines` to control how many content rows to render (default 3).
 * Use `showHeader` (default true) to toggle the title bar placeholder.
 */
export function SkeletonCard({
  lines = 3,
  showHeader = true,
}: {
  lines?: number;
  showHeader?: boolean;
}) {
  return (
    <div
      className="rounded-lg border border-slate-800 bg-slate-900 p-4"
      aria-hidden="true"
      data-testid="skeleton-card"
    >
      {showHeader && (
        <div className="mb-3 h-4 w-2/5 animate-pulse rounded bg-slate-700" />
      )}
      <div className="space-y-2">
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={`h-3 animate-pulse rounded bg-slate-800 ${
              i === lines - 1 ? 'w-3/5' : 'w-full'
            }`}
          />
        ))}
      </div>
    </div>
  );
}
