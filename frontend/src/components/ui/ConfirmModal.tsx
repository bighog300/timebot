import { Button } from '@/components/ui/Button';

export function ConfirmModal({ open, title, description, onConfirm, onCancel }: { open: boolean; title: string; description: string; onConfirm: () => void; onCancel: () => void }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-md rounded-lg border border-slate-700 bg-slate-900 p-4">
        <h3 className="text-lg font-semibold">{title}</h3>
        <p className="mt-2 text-sm text-slate-300">{description}</p>
        <div className="mt-4 flex justify-end gap-2">
          <Button className="bg-slate-700 hover:bg-slate-600" onClick={onCancel}>Cancel</Button>
          <Button className="bg-red-700 hover:bg-red-600" onClick={onConfirm}>Confirm</Button>
        </div>
      </div>
    </div>
  );
}

