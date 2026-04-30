import { Button } from '@/components/ui/Button';

export function PaginationControls({
  page,
  total,
  hasNext = true,
  onPrev,
  onNext,
}: {
  page: number;
  total?: number;
  hasNext?: boolean;
  onPrev: () => void;
  onNext: () => void;
}) {
  const totalPages = total ?? null;
  return (
    <div className="mt-3 flex items-center justify-end gap-2 text-sm text-slate-300">
      <span>Page {page + 1}{totalPages ? ` of ${totalPages}` : ''}</span>
      <Button onClick={onPrev} disabled={page <= 0}>Prev</Button>
      <Button onClick={onNext} disabled={totalPages ? page + 1 >= totalPages : !hasNext}>Next</Button>
    </div>
  );
}

