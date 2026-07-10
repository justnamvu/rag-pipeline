import { useState } from 'react'
import UploadPanel from './components/UploadPanel'
import ChatInterface from './components/ChatInterface'

function App() {
  const [uploadedDocs, setUploadedDocs] = useState([])
  const [sidebarOpen, setSidebarOpen] = useState(true)

  function handleDocumentUploaded(doc) {
    setUploadedDocs(prev => [doc, ...prev])
  }

  return (
    <div className="flex h-screen bg-white text-gray-900">
      {/* Sidebar */}
      <aside className={`
          shrink-0 border-r border-gray-200 flex flex-col
          transition-all duration-200
          ${sidebarOpen ? 'w-72' : 'w-0 overflow-hidden border-r-0'}
      `}>
        <div className="px-4 py-4 border-b border-gray-200 flex items-center
                        justify-between"
        >
          <h1 className="text-sm font-medium text-gray-900">RAG</h1>
        </div>
        <div className="flex-1 overflow-y-auto px-3 py-3 min-w-72">
          <UploadPanel onDocumentUploaded={handleDocumentUploaded} />
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col min-h-0 min-w-0">
        {/* Top bar with sidebar toggle */}
        <div className="flex items-center gap-3 px-4 py-3 border-b
                        border-gray-200">
          <button
            onClick={() => setSidebarOpen(prev => !prev)}
            className="text-gray-400 hover:text-gray-600 transition-colors
                        p-1 rounded-md hover:bg-gray-100"
            aria-label="Toggle sidebar"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24"
              stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round"
                d="M4 6h16M4 12h16M4 18h16"/>
            </svg>
          </button>
          <span className="text-sm text-gray-400">
            {uploadedDocs.length > 0
              ? `${uploadedDocs.length} document${uploadedDocs.length !== 1? 's' : ''} ready`
              : 'No documents uploaded'}
          </span>
        </div>

        <ChatInterface hasDocuments={uploadedDocs.length > 0}/>
      </main>
    </div>
  )
}

export default App