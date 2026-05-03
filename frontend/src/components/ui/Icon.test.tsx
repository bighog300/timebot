import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { Icon } from './Icon';

describe('Icon', () => {
  it('renders an SVG element', () => {
    const { container } = render(<Icon name="dashboard" />);
    expect(container.querySelector('svg')).toBeTruthy();
  });

  it('applies custom size', () => {
    const { container } = render(<Icon name="search" size={24} />);
    const svg = container.querySelector('svg');
    expect(svg?.getAttribute('width')).toBe('24');
    expect(svg?.getAttribute('height')).toBe('24');
  });

  it('is aria-hidden', () => {
    const { container } = render(<Icon name="settings" />);
    expect(container.querySelector('[aria-hidden="true"]')).toBeTruthy();
  });
});
