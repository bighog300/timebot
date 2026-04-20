import { useCategories } from '@/hooks/useApi';
import { Card } from '@/components/ui/Card';

export function CategoriesPage() {
  const { data } = useCategories();
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Categories</h1>
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
