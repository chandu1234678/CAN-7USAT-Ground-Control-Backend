import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import App from './App';

vi.mock('./components/Dashboard', () => ({
  Dashboard: () => <div>Dashboard Rendered</div>,
}));

describe('App', () => {
  it('renders the dashboard root component', () => {
    render(<App />);
    expect(screen.getByText('Dashboard Rendered')).toBeInTheDocument();
  });
});
