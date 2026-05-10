import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vite-plus/test';

import { CodePanel } from './CodePanel.js';

describe('CodePanel', () => {
  it('has the open class when open is true', () => {
    const { container } = render(<CodePanel open code="stand()" />);
    expect(container.querySelector('#code-panel')).toHaveClass('open');
  });

  it('does not have the open class when open is false', () => {
    const { container } = render(<CodePanel open={false} code="stand()" />);
    expect(container.querySelector('#code-panel')).not.toHaveClass('open');
  });

  it('renders the Generated Python header', () => {
    render(<CodePanel open code="stand()" />);
    expect(screen.getByText('Generated Python')).toBeInTheDocument();
  });
});
