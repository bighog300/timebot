import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LoadingState, EmptyState, ErrorState, SkeletonCard } from './States';

describe('States', () => {
  it('LoadingState renders label', () => {
    render(<LoadingState label="Loading data..." />);
    expect(screen.getByText('Loading data...')).toBeTruthy();
  });

  it('EmptyState renders label', () => {
    render(<EmptyState label="Nothing here." />);
    expect(screen.getByText('Nothing here.')).toBeTruthy();
  });

  it('ErrorState renders message', () => {
    render(<ErrorState message="Something went wrong." />);
    expect(screen.getByText('Something went wrong.')).toBeTruthy();
  });

  it('SkeletonCard renders with default props', () => {
    render(<SkeletonCard />);
    expect(screen.getByTestId('skeleton-card')).toBeTruthy();
  });

  it('SkeletonCard renders correct number of line placeholders', () => {
    const { container } = render(<SkeletonCard lines={5} showHeader={false} />);
    // 5 line divs inside the space-y-2 container
    const lines = container.querySelectorAll('.h-3.animate-pulse');
    expect(lines.length).toBe(5);
  });
});
