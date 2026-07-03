import { useState } from 'react'
import UploadPanel from './components/UploadPanel'
import ChatInterface from './components/ChatInterface'

function App() {
  const [uploadedDocs, setUploadedDocs] = useState([])

  function handleDocumentUploaded(doc) {
    setUploadedDocs(prev => [doc, ...prev])
  }

  return (
    <div className="flex h-screen bg-white text-gray-900">
      {/* Sidebar */}
      <aside className="w-72 shrink-0 border-r border-gray-200 flex flex-col">
        <div className="px-4 py-4 border-b border-gray-200">
          <h1 className="text-sm font-medium text-gray-900">NodeRAG</h1>
        </div>
        <div className="flex-1 overflow-y-auto px-3 py-3">
          <UploadPanel onDocumentUploaded={handleDocumentUploaded} />
        </div>
      </aside>

      {/* Main chat panel */}
      <main className="flex-1 flex flex-col min-h-0">
        <ChatInterface hasDocuments={uploadedDocs.length > 0}/>
      </main>
    </div>
  )
}

export default App