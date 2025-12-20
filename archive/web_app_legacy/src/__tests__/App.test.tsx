import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from '../App';

describe('App Component', () => {
    it('renders without crashing', () => {
        render(<App />);
        // Basic check to see if the main container or some text exists
        // Adjust expectation based on App.tsx content
        expect(document.body).toBeTruthy();
    });
});
