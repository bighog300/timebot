import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PageHeader, ResponsiveGrid, ResponsivePage, StickyActionBar } from './ResponsiveLayout';

describe('Responsive layout helpers', () => {
  it('renders children', () => {
    render(
      <ResponsivePage>
        <PageHeader>
          <h1>Header</h1>
        </PageHeader>
        <ResponsiveGrid>
          <div>Left</div>
          <div>Right</div>
        </ResponsiveGrid>
      </ResponsivePage>,
    );

    expect(screen.getByText('Header')).toBeTruthy();
    expect(screen.getByText('Left')).toBeTruthy();
    expect(screen.getByText('Right')).toBeTruthy();
  });

  it('includes responsive class behavior', () => {
    const { container } = render(
      <>
        <ResponsivePage><div>Page</div></ResponsivePage>
        <PageHeader><div>Head</div></PageHeader>
        <ResponsiveGrid><div>A</div><div>B</div></ResponsiveGrid>
        <StickyActionBar><button type="button">Action</button></StickyActionBar>
      </>,
    );

    expect(container.querySelector('.sm\\:px-6')).toBeTruthy();
    expect(container.querySelector('.sm\\:flex-row')).toBeTruthy();
    expect(container.innerHTML.includes('md:grid-cols-[360px_minmax(0,1fr)]')).toBe(true);
    expect(container.querySelector('.sticky.bottom-0')).toBeTruthy();
  });
});
