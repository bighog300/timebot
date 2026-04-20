export function LoadingState({ label = 'Loading...' }: { label?: string }) {
  return <div className="animate-pulse text-sm text-slate-400">{label}</div>;
}

export function EmptyState({ label }: { label: string }) {
  return <div className="rounded border border-dashed border-slate-700 p-8 text-center text-slate-400">{label}</div>;
}

export function ErrorState({ message }: { message: string }) {
  return <div className="rounded border border-red-800 bg-red-950/40 p-4 text-red-300">{message}</div>;
}
