import { useState } from 'react'
import UploadPanel from './components/UploadPanel'
import ChatInterface from './components/ChatInterface'

function SidebarIcon({ open }) {
  return (
    <svg
      className="w-[18px] h-[18px]"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={1.75}
    >
      <rect x="3" y="4" width="18" height="16" rx="2.5" strokeLinejoin="round" />
      <line
        x1="9.5"
        y1="4"
        x2="9.5"
        y2="20"
        className={`origin-center transition-transform duration-200 ${
          open ? '' : '-translate-x-[2px]'
        }`}
      />
    </svg>
  )
}

function App() {
  const [uploadedDocs, setUploadedDocs] = useState([])
  const [sidebarOpen, setSidebarOpen] = useState(true)

  function handleDocumentUploaded(doc) {
    setUploadedDocs(prev => [doc, ...prev])
  }

  return (
    <div className="flex h-screen bg-white text-gray-900">
      {/* Sidebar (collapses to a 56px rail so the toggle always lives here) */}
      <aside
        className={`shrink-0 border-r border-gray-200 bg-gray-50/60 flex flex-col
                    transition-[width] duration-200 ease-out
                    ${sidebarOpen ? 'w-80' : 'w-14'}`}
      >
        <div
          className={`h-14 shrink-0 flex items-center border-b border-gray-200 px-3
                      ${sidebarOpen ? 'justify-between' : 'justify-center'}`}
        >
          {sidebarOpen && (
            <div className="flex items-center gap-2 pl-1">
              <h1 className="text-[15px] font-medium tracking-tight text-gray-900">
                RAG Pipeline
              </h1>
            </div>
          )}
          <button
            onClick={() => setSidebarOpen(prev => !prev)}
            className="p-1.5 rounded-lg text-gray-500 hover:text-gray-900
                       hover:bg-gray-200/70 active:scale-95
                       transition-all duration-150"
            aria-label={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
            title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          >
            <SidebarIcon open={sidebarOpen} />
          </button>
        </div>

        <div
          className={`flex-1 overflow-y-auto overflow-x-hidden px-3 py-3
                      transition-opacity duration-150
                      ${sidebarOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
        >
          <div className="w-[296px]">
            <UploadPanel onDocumentUploaded={handleDocumentUploaded} />
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col min-h-0 min-w-0">
        <div className="h-14 shrink-0 flex items-center px-6 border-b border-gray-200">
          <span className="flex items-center gap-2 text-[14px] text-gray-500">
            <span
              className={`w-1.5 h-1.5 rounded-full transition-colors ${
                uploadedDocs.length > 0 ? 'bg-green-500' : 'bg-gray-300'
              }`}
            />
            {uploadedDocs.length > 0
              ? `${uploadedDocs.length} document${uploadedDocs.length !== 1 ? 's' : ''} ready`
              : 'No documents uploaded'}
          </span>
        </div>

        <ChatInterface hasDocuments={uploadedDocs.length > 0} />
      </main>
    </div>
  )
}

export default App
