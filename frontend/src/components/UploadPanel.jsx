import { useState, useRef } from 'react'
import { uploadDocument } from '../api'

const ACCEPTED_TYPES = [
  'application/pdf',
  'text/plain',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
]

const ACCEPTED_EXTENSIONS = '.pdf,.txt,.docx'

const STATUS = {
  uploading: { label: 'Uploading', color: 'text-blue-600 bg-blue-50' },
  success: { label: 'Ready', color: 'text-green-700 bg-green-50' },
  error: { label: 'Failed', color: 'text-red-600 bg-red-50' },
}

export default function UploadPanel({ onDocumentUploaded }) {
  const [documents, setDocuments] = useState([])
  const [dragActive, setDragActive] = useState(false)
  const inputRef = useRef(null)

  function updateDocument(filename, patch) {
    setDocuments(prev =>
      prev.map(doc => (doc.filename === filename ? { ...doc, ...patch } : doc))
    )
  }

  async function uploadFile(file) {
    if (!ACCEPTED_TYPES.includes(file.type)) {
      alert(`Unsupported file type: ${file.name}`)
      return
    }

    setDocuments(prev => [
      { filename: file.name, status: 'uploading', chunkCount: null },
      ...prev.filter(d => d.filename !== file.name),
    ])

    try {
      const data = await uploadDocument(file)
      updateDocument(file.name, {
        status: 'success',
        chunkCount: data.chunk_count,
        docId: data.doc_id,
      })
      onDocumentUploaded?.(data)
    } catch (err) {
      updateDocument(file.name, { status: 'error', error: err.message })
    }
  }

  function handleFiles(files) {
    Array.from(files).forEach(uploadFile)
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragActive(false)
    handleFiles(e.dataTransfer.files)
  }

  function handleDragOver(e) {
    e.preventDefault()
    setDragActive(true)
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Drop zone */}
      <div
        onClick={() => inputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={() => setDragActive(false)}
        className={`border border-dashed rounded-xl px-4 py-6 text-center cursor-pointer
                    transition-all duration-150 ${
                      dragActive
                        ? 'border-blue-400 bg-blue-50 scale-[1.01]'
                        : 'border-gray-300 bg-white hover:border-gray-400 hover:bg-gray-50'
                    }`}
      >
        <svg
          className={`w-5 h-5 mx-auto mb-2 transition-colors ${
            dragActive ? 'text-blue-500' : 'text-gray-400'
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.75}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 16V4m-5 5 5-5 5 5M4 17v2a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-2" />
        </svg>
        <p className="text-[13px] text-gray-700 leading-relaxed">
          Drop a file here or <span className="text-blue-600 font-medium">browse</span>
        </p>
        <p className="text-xs text-gray-500 mt-1">PDF, DOCX, TXT</p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPTED_EXTENSIONS}
          className="hidden"
          onChange={e => {
            handleFiles(e.target.files)
            e.target.value = '' // allow re-uploading the same file
          }}
        />
      </div>

      {/* Document list */}
      {documents.length > 0 && (
        <ul className="flex flex-col gap-1.5">
          {documents.map(doc =>
            doc.status === 'uploading' ? (
              <li key={doc.filename}>
                <SkeletonItem />
              </li>
            ) : (
              <li
                key={doc.filename}
                className="flex items-start justify-between gap-2 px-3 py-2.5 rounded-lg
                           bg-white border border-gray-200 hover:border-gray-300
                           transition-colors"
              >
                <div className="flex flex-col min-w-0">
                  <span className="text-[13px] font-medium text-gray-900 truncate">
                    {doc.filename}
                  </span>
                  {doc.chunkCount != null && (
                    <span className="text-xs text-gray-500 mt-0.5">{doc.chunkCount} chunks</span>
                  )}
                  {doc.error && (
                    <span className="text-xs text-red-500 mt-0.5 line-clamp-2">{doc.error}</span>
                  )}
                </div>
                <span
                  className={`text-[11px] font-medium shrink-0 px-1.5 py-0.5 rounded-md
                              ${STATUS[doc.status].color}`}
                >
                  {STATUS[doc.status].label}
                </span>
              </li>
            )
          )}
        </ul>
      )}
    </div>
  )
}

function SkeletonItem() {
  return (
    <div className="flex items-center justify-between px-3 py-2.5 rounded-lg
                    border border-gray-200 bg-white animate-pulse">
      <div className="flex flex-col gap-1.5 flex-1">
        <div className="h-2.5 bg-gray-200 rounded w-3/4" />
        <div className="h-2 bg-gray-100 rounded w-1/3" />
      </div>
      <div className="h-2 bg-gray-200 rounded w-10 ml-2" />
    </div>
  )
}
