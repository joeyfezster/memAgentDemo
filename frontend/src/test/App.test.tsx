import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from '../App'

describe('App', () => {
  it('renders the app header', () => {
    render(<App />)
    expect(screen.getByText('Memory Agent')).toBeInTheDocument()
  })

  it('increments counter on button click', () => {
    render(<App />)
    const button = screen.getByRole('button', { name: /count:/i })
    expect(button).toHaveTextContent('Count: 0')

    fireEvent.click(button)
    expect(button).toHaveTextContent('Count: 1')

    fireEvent.click(button)
    expect(button).toHaveTextContent('Count: 2')
  })
})
