import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'

// Basic test to verify testing infrastructure
describe('Frontend Testing Infrastructure', () => {
  it('should be able to render a basic component', () => {
    const TestComponent = () => <div>Test Component</div>
    render(<TestComponent />)
    expect(screen.getByText('Test Component')).toBeInTheDocument()
  })

  it('should handle basic React hooks', () => {
    const { useState } = require('react')
    const TestComponent = () => {
      const [count, setCount] = useState(0)
      return (
        <div>
          <span>Count: {count}</span>
          <button onClick={() => setCount(count + 1)}>Increment</button>
        </div>
      )
    }
    
    render(<TestComponent />)
    expect(screen.getByText('Count: 0')).toBeInTheDocument()
  })
})