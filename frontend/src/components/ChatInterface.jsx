import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { queryDocuments } from '../api'

const MAX_SOURCES = 3

export default function ChatInterface({ hasDocuments }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function sendMessage(overrideQuery) {
    const query = (overrideQuery ?? input).trim()
    if (!query || loading) return

    setMessages(prev => [...prev, { role: 'user', content: query }])
    setInput('')
    setLoading(true)

    try {
      const data = await queryDocuments(query, { topK: 5 })
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: data.answer, sources: data.sources ?? [] },
      ])
    } catch (err) {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: null, error: err.message, retryQuery: query },
      ])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const canSend = !loading && input.trim() && hasDocuments

  return (
    <div className="flex flex-col h-full">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto px-6 py-8">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center gap-2">
            <p className="text-lg font-medium tracking-tight text-gray-800">
              {hasDocuments ? 'Ask a question about your documents' : 'Upload a document to get started'}
            </p>
            <p className="text-sm text-gray-500">
              {hasDocuments
                ? 'Answers are grounded in what you uploaded'
                : 'PDF, DOCX, or TXT - drop one in the sidebar'}
            </p>
          </div>
        ) : (
          <div className="max-w-2xl mx-auto flex flex-col gap-6">
            {messages.map((msg, i) => (
              <Message
                key={i}
                message={msg}
                onRetry={query => {
                  setMessages(prev => prev.filter((_, idx) => idx !== i))
                  sendMessage(query)
                }}
              />
            ))}

            {loading && <ThinkingDots />}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Input bar */}
      <div className="border-t border-gray-200 px-6 py-4">
        <div className="max-w-2xl mx-auto">
          <div
            className={`flex items-end gap-2 border rounded-2xl pl-4 pr-2 py-2
                        transition-all duration-150 ${
                          loading
                            ? 'border-gray-200 bg-gray-50'
                            : 'border-gray-300 bg-white focus-within:border-blue-400 focus-within:ring-4 focus-within:ring-blue-500/10'
                        }`}
          >
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                hasDocuments ? 'Ask a question about your documents...' : 'Upload a document first'
              }
              disabled={loading || !hasDocuments}
              className="flex-1 py-2 text-[15px] text-gray-900 outline-none bg-transparent
                         placeholder:text-gray-400 disabled:cursor-not-allowed"
            />
            <button
              onClick={() => sendMessage()}
              disabled={!canSend}
              aria-label="Send message"
              className={`shrink-0 w-9 h-9 rounded-xl flex items-center justify-center
                          transition-all duration-150 ${
                            canSend
                              ? 'bg-blue-500 text-white hover:bg-blue-600 active:scale-95'
                              : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                          }`}
            >
              {loading ? <Spinner /> : <ArrowUpIcon />}
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-2 text-center">
            Answers are grounded in your uploaded documents
          </p>
        </div>
      </div>
    </div>
  )
}

function Message({ message, onRetry }) {
  const isUser = message.role === 'user'
  const [sourcesOpen, setSourcesOpen] = useState(false)

  // Backend returns sources sorted by score desc; show only the top 3
  const topSources = (message.sources ?? []).slice(0, MAX_SOURCES)

  return (
    <div className={`flex flex-col animate-[fadeIn_200ms_ease-out] ${isUser ? 'items-end' : 'items-start'}`}>
      <div
        className={`rounded-2xl px-4 py-3 max-w-prose text-[15px] leading-relaxed ${
          isUser
            ? 'bg-blue-500 text-white rounded-tr-sm'
            : 'bg-gray-100 text-gray-900 rounded-tl-sm'
        }`}
      >
        {message.error ? (
          <div className="flex flex-col gap-2">
            <p className="text-sm text-red-600">{message.error}</p>
            {message.retryQuery && (
              <button
                onClick={() => onRetry(message.retryQuery)}
                className="text-xs text-gray-500 hover:text-gray-900 underline
                           underline-offset-2 self-start transition-colors"
              >
                Retry
              </button>
            )}
          </div>
        ) : isUser ? (
          <p>{message.content}</p>
        ) : (
          <div className="prose prose-sm max-w-none prose-p:text-gray-900 prose-li:text-gray-900
                          prose-headings:text-gray-900 prose-strong:text-gray-900">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
      </div>

      {!isUser && topSources.length > 0 && (
        <div className="mt-2 w-full max-w-prose">
          <button
            onClick={() => setSourcesOpen(prev => !prev)}
            className="text-[13px] text-gray-500 hover:text-gray-900 transition-colors
                       flex items-center gap-1.5 rounded-md px-1.5 py-1 hover:bg-gray-100"
          >
            <svg
              className={`w-3 h-3 transition-transform duration-200 ${sourcesOpen ? 'rotate-90' : ''}`}
              viewBox="0 0 12 12"
              fill="currentColor"
            >
              <path d="M4 2.5 8 6l-4 3.5z" />
            </svg>
            {topSources.length} source{topSources.length !== 1 ? 's' : ''}
          </button>

          {sourcesOpen && (
            <ul className="mt-2 flex flex-col gap-2">
              {topSources.map((source, i) => (
                <li
                  key={i}
                  className="text-[13px] border border-gray-200 rounded-lg px-3 py-2 bg-white
                             hover:border-gray-300 transition-colors"
                >
                  <p className="font-medium text-gray-800 mb-1">
                    {source.filename}
                    <span className="text-gray-500 font-normal ml-1">
                      ⋅ chunk {source.chunk_index} ⋅ score {source.score?.toFixed(3)}
                    </span>
                  </p>
                  <p className="text-gray-600 leading-relaxed line-clamp-3">{source.chunk_text}</p>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}

function ArrowUpIcon() {
  return (
    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.25}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 19V5M5 12l7-7 7 7" />
    </svg>
  )
}

function Spinner() {
  return (
    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
    </svg>
  )
}

function ThinkingDots() {
  return (
    <div className="flex items-center gap-1 px-4 py-3.5 bg-gray-100 rounded-2xl rounded-tl-sm self-start">
      {[0, 1, 2].map(i => (
        <span
          key={i}
          className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
          style={{ animationDelay: `${i * 150}ms` }}
        />
      ))}
    </div>
  )
}
