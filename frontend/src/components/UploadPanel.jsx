import { useState, useRef } from 'react'

const ACCEPTED_TYPES = ['application/pdf', 'text/plain',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document']

const ACCEPTED_EXTENSIONS = '.pdf,.txt,.docx'

const STATUS = {
    uploading: { label: 'Uploading...', color: 'text-blue-500' },
    success: { label: 'Ready', color: 'text-green-600'},
    error: { label: 'Failed', color: 'text-red-500' },
}

export default function UploadPanel({ onDocumentUploaded }) {
    const [documents, setDocuments] = useState([])
    const [dragActive, setDragActive] = useState(false)
    const inputRef = useRef(null)

    function updateDocument(filename, patch) {
        setDocuments(prev =>
            prev.map(doc => doc.filename === filename ? {...doc, ...patch} : doc)
        )
    }

    async function uploadFile(file) {
        if (!ACCEPTED_TYPES.includes(file.type)) {
            alert(`Unsupported file type: ${file.name}`)
            return
        }
        
        setDocuments(prev => [
            { filename: file.name, status: 'uploading', chunkCount: null },
            ...prev,
        ])

        const formData = new FormData()
        formData.append('file', file)

        try {
            const res = await fetch('http://localhost:8000/api/v1/upload', {
                method: 'POST',
                body: formData,
            })

            if (!res.ok) {
                const err = await res.json()
                throw new Error(err.detail || 'Upload failed')
            }

            const data = await res.json()
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
                className={`
                    border border-dashed rounded-xl px-4 py-5 text-center cursor-pointer
                    transition-colors duration-150
                    ${dragActive
                        ? 'border-blue-400 bg-blue-50'
                        : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
                    }
                `}
            >
                <p className="text-xs text-gray-500 leading-relaxed">
                    Drop a file here or {' '}
                    <span className="text-blue-500 font-medium">browse</span>
                </p>
                <p className="text-xs text-gray-400 mt-1">PDF, DOCX, TXT</p>
                <input 
                    ref={inputRef}
                    type="file"
                    accept={ACCEPTED_EXTENSIONS}
                    className="hidden"
                    onChange={e => handleFiles(e.target.files)}
                />
            </div>

            {/* Document list */}
            {documents.length > 0 && (
                <ul className="flex flex-col gap-1">
                    {documents.map(doc => (
                        doc.status === 'uploading' ? (
                            <li key={doc.filename}>
                                <SkeletonItem />
                            </li>
                        ) : (
                            <li
                                key={doc.filename}
                                className="flex items-start justify-between gap-2
                                            px-3 py-2 rounded-lg bg-gray-50 border
                                            border-gray-200"
                            >
                                <div className="flex flex-col min-w-0">
                                    <span className="text-xs font-medium text-gray-800 truncate">
                                        {doc.filename}
                                    </span>
                                    {doc.chunkCount !== null && (
                                        <span className="text-xs text-gray-400">
                                            {doc.chunkCount} chunks
                                        </span>
                                    )}
                                    {doc.error && (
                                        <span className="text-xs text-red-400 truncate">
                                            {doc.error}
                                        </span>
                                    )}
                                </div>
                                <span className={`text-xs shrink-0 mt-0.5 ${STATUS[doc.status].color}`}>
                                    {STATUS[doc.status].label}
                                </span>
                            </li>
                        )
                    ))}
                </ul>
            )}
        </div> 
    )
}

function SkeletonItem() {
    return (
        <div className="flex items-center justify-between px-3 py-2 rounded-lg
                        border border-gray-100 bg-gray-50 animate-pulse">
            <div className="flex flex-col gap-1.5 flex-1">
                <div className="h-2.5 bg-gray-200 rounded w-3/4" />
                <div className="h-2 bg-gray-100 rounded w-1/3" />
            </div>
            <div className="h-2 bg-gray-200 rounded w-10 ml-2" />
        </div>
    )
}