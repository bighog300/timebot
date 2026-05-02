import { useCategories } from '@/hooks/useApi';
import { Card } from '@/components/ui/Card';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/States';
import { getUserFacingErrorMessage } from '@/lib/errors';

export function CategoriesPage() {
  const { data, isLoading, isError, error } = useCategories();
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Categories</h1>
      {isLoading && <LoadingState />}
      {isError && <ErrorState message={getUserFacingErrorMessage(error, 'Failed to load categories')} />}
      {!isLoading && !isError && (data?.length ?? 0) === 0 && <EmptyState label="No categories available." />}
      <div className="grid gap-3 md:grid-cols-2">
        {data?.map((cat) => (
          <Card key={cat.id}>
            <div className="flex items-center justify-between">
              <span>{cat.name}</span>
              <span className="text-xs text-slate-400">{cat.document_count}</span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
