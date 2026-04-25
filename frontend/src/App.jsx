import { useEffect, useState } from "react"
import axios from "axios"

export default function App() {
  const [status, setStatus] = useState(null)

  useEffect(() => {
    axios.get("http://localhost:8000/health")
      .then(r => setStatus(r.data.status))
      .catch(() => setStatus("bağlantı hatası"))
  }, [])

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-10 text-center">
        <h1 className="text-3xl font-bold text-white mb-2">
          Virtual Try-On
        </h1>
        <p className="text-gray-400 mb-4">AI-Powered Fashion Assistant</p>
        <div className="flex items-center justify-center gap-2">
          <div className={`w-2 h-2 rounded-full ${status === 'ok' ? 'bg-green-500' : 'bg-red-500'}`}/>
          <span className="text-sm text-gray-400">
            API: {status ?? "bağlanıyor..."}
          </span>
        </div>
      </div>
    </div>
  )
}