import { Link } from 'react-router-dom';

export function UpgradePrompt({ title, message }: { title?: string; message: string }) {
  return (
    <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-3 text-sm">
      {title ? <div className="mb-1 font-semibold text-amber-200">{title}</div> : null}
      <div className="text-slate-200">{message}</div>
      <div className="mt-2">
        <Link className="rounded bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white" to="/upgrade">
          View plans
        </Link>
      </div>
    </div>
  );
}
