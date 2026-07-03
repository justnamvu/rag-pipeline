import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'

export default function ChatInterface({ hasDocuments }) {
    const [messages, setMessages] = useState([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const bottomRef = useRef(null)

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    async function sendMessage(overrideQuery) {
        const query = overrideQuery || input.trim()
        if (!query || loading ) return

        setMessages(prev => [...prev, { role: 'user', content: query}])
        setInput('')
        setLoading(true)

        try {
            const res = await fetch('http://localhost:8000/api/v1/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, top_k: 5 }),
            })

            if (!res.ok) {
                const err = await res.json()
                throw new Error(err.detail || 'Query failed')
            }

            const data = await res.json()
            setMessages(prev => [
                ...prev,
                { role: 'assistant', content: data.answer, sources: data.sources},
            ])
        } catch (err) {
            setMessages(prev => [
                ...prev,
                { 
                    role: 'assistant', 
                    content: null, 
                    error: err.message,
                    retryQuery: query,
                },
            ])
        } finally {
            setLoading(false)
        }
    }

    function handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            sendMessage()
        }
    }

    return (
        <div className='flex flex-col h-full'>
            {/* Message list */}
            <div className="flex-1 overflow-y-auto px-6 py-6">
                {messages.length === 0 ? (
                    <div className="h-full flex items-center justify-center">
                        <p className="text-sm text-gray-400">
                            {hasDocuments
                                ? 'Ask a question about your documents'
                                : 'Upload a document to get started'
                            }
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
                                    setInput(query)
                                    setTimeout(() => sendMessage(query), 50)
                                }}
                            
                            />
                        ))}

                        {/* Thinking indicator */}
                        {loading && (
                            <div className="flex items-center gap-2">
                                <ThinkingDots />
                            </div>
                        )}

                        {/* Invisible anchor for auto-scroll */}
                        <div ref={bottomRef} />
                    </div>
                )}
            </div>

            {/* Input bar */}
            <div className="border-t border-gray-200 px-6 py-4">
                <div className="max-w-2xl mx-auto">
                    <div className={`flex items-center gap-2 border rounded-xl px-4 py-3
                        transition-colors ${loading
                            ? 'border-gray-200 bg-gray-50'
                            : 'border-gray-300 focus-within:border-blue-400'
                        }`}
                    >
                        <input
                            type="text"
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Ask a question about your documents..."
                            disabled={loading || !hasDocuments}
                            className="flex-1 text-sm outline-none placeholder:text-gray-400
                                        bg-transparent disabled:cursor-not-allowed"
                        />
                        <button
                            onClick={() => sendMessage()}
                            disabled={loading || !input.trim() || !hasDocuments}
                            className="min-w-[48px] flex items-center justify-center
                                        text-sm font-medium transition-colors
                                        text-blue-500 hover:text-blue-600
                                        disabled:text-gray-300 disabled:cursor-not-allowed"
                        >
                            {loading ? (
                                <svg
                                    className="animate-spin h-4 w-4 text-gray-400"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                >
                                    <circle
                                        className="opacity-25"
                                        cx="12" cy="12" r="10"
                                        stroke="currentColor"
                                        strokeWidth="4"
                                    />
                                    <path
                                        className="opacity-75"
                                        fill="currentColor"
                                        d="M4 12a8 8 0 018-8v8z"
                                    />
                                </svg>
                            ) : 'Send'}
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

    return (
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
            {/* Bubble */}
            <div className={`rounded-2xl px-4 py-3 max-w-prose text-sm leading-relaxed
                ${isUser
                    ? 'bg-blue-500 text-white rounded-tr-sm'
                    : 'bg-gray-100 text-gray-900 rounded-tl-sm'
                }`}
            >
                {message.error ? (
                    <div className="flex flex-col gap-2">
                        <p className="text-red-500 text-sm">{message.error}</p>
                        {message.retryQuery && (
                            <button
                                onClick={() => onRetry(message.retryQuery)}
                                className="text-xs text-gray-400 hover:text-gray-600
                                            underline underline-offset-2 self-start"
                            >
                                Retry
                            </button>
                        )}
                    </div>
                ) : isUser ? (
                    <p>{message.content}</p>
                ) : (
                    <div className="prose prose-sm max-w-none">
                        <ReactMarkdown>{message.content}</ReactMarkdown>
                    </div>
                )}
            </div>

            {/* Sources (only on assistant messages with sources */}
            {!isUser && message.sources?.length > 0 && (
                <div className="mt-2 w-full max-w-prose">
                    <button
                        onClick={() => setSourcesOpen(prev => !prev)}
                        className="text-xs text-gray-400 hover:text-gray-600
                                    transition-colors flex items-center gap-1"
                    >
                        <span>{sourcesOpen ? '↓' : '→'}</span>
                        {message.sources.length} source
                        {message.sources.length !== 1 ? 's' : ''}
                    </button>

                    {sourcesOpen && (
                        <ul className="mt-2 flex flex-col gap-2">
                            {message.sources.map((source, i) => (
                                <li
                                    key={i}
                                    className="text-xs border border-gray-200 rounded-lg
                                                px-3 py-2 bg-white"
                                >
                                    <p className="font-medium text-gray-700 mb-1">
                                        {source.filename}
                                        <span className="text-gray-400 font-normal ml-1">
                                            ⋅ chunk {source.chunk_index}
                                            ⋅ score {source.score.toFixed(3)}
                                        </span>
                                    </p>
                                    <p className="text-gray-500 leading-relaxed line-clamp-3">
                                        {source.chunk_text}
                                    </p>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            )}
        </div>
    )
}

function ThinkingDots() {
    return (
        <div className="flex items-center gap-1 px-4 py-3 bg-gray-100
                        rounded-2xl rounded-tl-sm">
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