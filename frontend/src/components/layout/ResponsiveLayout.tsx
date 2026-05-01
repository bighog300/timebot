import type { ReactNode } from 'react';

type ChildrenOnly = { children: ReactNode };

export function ResponsivePage({ children }: ChildrenOnly) {
  return <div className="mx-auto w-full max-w-7xl space-y-4 px-4 sm:px-6 lg:px-8">{children}</div>;
}

export function PageHeader({ children }: ChildrenOnly) {
  return <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">{children}</header>;
}

export function ResponsiveGrid({ children }: ChildrenOnly) {
  return <div className="grid gap-4 md:grid-cols-[360px_minmax(0,1fr)]">{children}</div>;
}

export function StickyActionBar({ children }: ChildrenOnly) {
  return <div className="sticky bottom-0 z-10 -mx-4 border-t border-slate-700 bg-slate-950/90 px-4 py-3 backdrop-blur sm:-mx-6 sm:px-6 lg:-mx-8 lg:px-8">{children}</div>;
}
