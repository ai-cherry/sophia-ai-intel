import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChatInterface } from '../ChatInterface'
import { WebSocketProvider } from '@/contexts/WebSocketContext'

// Mock the WebSocket context
jest.mock('@/contexts/WebSocketContext', () => ({
  useWebSocket: () => ({
    connected: true,
    send: jest.fn(),
    subscribe: jest.fn(),
    unsubscribe: jest.fn(),
  }),
  WebSocketProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

describe('ChatInterface', () => {
  const mockOnSendMessage = jest.fn()
  const mockOnClear = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders chat interface correctly', () => {
    render(
      <ChatInterface
        messages={[]}
        onSendMessage={mockOnSendMessage}
        onClear={mockOnClear}
      />
    )

    expect(screen.getByPlaceholderText(/type your message/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument()
  })

  it('displays messages correctly', () => {
    const messages = [
      { id: '1', role: 'user', content: 'Hello', timestamp: new Date() },
      { id: '2', role: 'assistant', content: 'Hi there!', timestamp: new Date() },
    ]

    render(
      <ChatInterface
        messages={messages}
        onSendMessage={mockOnSendMessage}
        onClear={mockOnClear}
      />
    )

    expect(screen.getByText('Hello')).toBeInTheDocument()
    expect(screen.getByText('Hi there!')).toBeInTheDocument()
  })

  it('sends message on form submission', async () => {
    const user = userEvent.setup()
    
    render(
      <ChatInterface
        messages={[]}
        onSendMessage={mockOnSendMessage}
        onClear={mockOnClear}
      />
    )

    const input = screen.getByPlaceholderText(/type your message/i)
    const sendButton = screen.getByRole('button', { name: /send/i })

    await user.type(input, 'Test message')
    await user.click(sendButton)

    expect(mockOnSendMessage).toHaveBeenCalledWith('Test message')
    expect(input).toHaveValue('')
  })

  it('sends message on Enter key press', async () => {
    const user = userEvent.setup()
    
    render(
      <ChatInterface
        messages={[]}
        onSendMessage={mockOnSendMessage}
        onClear={mockOnClear}
      />
    )

    const input = screen.getByPlaceholderText(/type your message/i)
    
    await user.type(input, 'Test message{Enter}')

    expect(mockOnSendMessage).toHaveBeenCalledWith('Test message')
  })

  it('does not send empty messages', async () => {
    const user = userEvent.setup()
    
    render(
      <ChatInterface
        messages={[]}
        onSendMessage={mockOnSendMessage}
        onClear={mockOnClear}
      />
    )

    const sendButton = screen.getByRole('button', { name: /send/i })
    await user.click(sendButton)

    expect(mockOnSendMessage).not.toHaveBeenCalled()
  })

  it('shows loading state while waiting for response', () => {
    render(
      <ChatInterface
        messages={[]}
        onSendMessage={mockOnSendMessage}
        onClear={mockOnClear}
        isLoading={true}
      />
    )

    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument()
  })

  it('handles markdown formatting in messages', () => {
    const messages = [
      {
        id: '1',
        role: 'assistant',
        content: '**Bold text** and *italic text*\n\n```python\nprint("Hello")\n```',
        timestamp: new Date(),
      },
    ]

    render(
      <ChatInterface
        messages={messages}
        onSendMessage={mockOnSendMessage}
        onClear={mockOnClear}
      />
    )

    expect(screen.getByText(/Bold text/)).toBeInTheDocument()
    expect(screen.getByText(/italic text/)).toBeInTheDocument()
    expect(screen.getByText(/print/)).toBeInTheDocument()
  })

  it('scrolls to bottom when new message arrives', async () => {
    const { rerender } = render(
      <ChatInterface
        messages={[]}
        onSendMessage={mockOnSendMessage}
        onClear={mockOnClear}
      />
    )

    const scrollIntoViewMock = jest.fn()
    window.HTMLElement.prototype.scrollIntoView = scrollIntoViewMock

    const newMessages = [
      { id: '1', role: 'user', content: 'New message', timestamp: new Date() },
    ]

    rerender(
      <ChatInterface
        messages={newMessages}
        onSendMessage={mockOnSendMessage}
        onClear={mockOnClear}
      />
    )

    await waitFor(() => {
      expect(scrollIntoViewMock).toHaveBeenCalled()
    })
  })

  it('clears chat history when clear button is clicked', async () => {
    const user = userEvent.setup()
    
    render(
      <ChatInterface
        messages={[
          { id: '1', role: 'user', content: 'Message', timestamp: new Date() },
        ]}
        onSendMessage={mockOnSendMessage}
        onClear={mockOnClear}
      />
    )

    const clearButton = screen.getByRole('button', { name: /clear/i })
    await user.click(clearButton)

    expect(mockOnClear).toHaveBeenCalled()
  })
})