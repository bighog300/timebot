import { Link } from 'react-router-dom';

export interface UpgradeRequirement {
  feature: string;
  requiredPlan: string;
  message: string;
}

export function UpgradeRequiredModal({ requirement, onClose }: { requirement: UpgradeRequirement | null; onClose: () => void }) {
  if (!requirement) return null;
  return (
    <div className="fixed inset-0 z-40 bg-black/60 p-4">
      <div className="mx-auto mt-20 max-w-md rounded border border-amber-500/40 bg-slate-900 p-4">
        <h3 className="text-lg font-semibold text-amber-200">Upgrade required</h3>
        <p className="mt-2 text-sm text-slate-100"><span className="font-semibold">Feature:</span> {requirement.feature}</p>
        <p className="text-sm text-slate-100"><span className="font-semibold">Required plan:</span> {requirement.requiredPlan}</p>
        <p className="mt-2 text-sm text-slate-300">{requirement.message}</p>
        <div className="mt-4 flex justify-end gap-2">
          <button className="rounded border border-slate-700 px-3 py-1.5 text-sm" onClick={onClose}>Close</button>
          <Link className="rounded bg-indigo-600 px-3 py-1.5 text-sm font-semibold text-white" to="/upgrade" onClick={onClose}>View plans</Link>
        </div>
      </div>
    </div>
  );
}
