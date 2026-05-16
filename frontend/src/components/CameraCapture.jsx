import { useRef, useState, useEffect } from "react"

export default function CameraCapture({ onCapture, onClose }) {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)
  const [ready, setReady] = useState(false)
  const [captured, setCaptured] = useState(null)
  const [error, setError] = useState("")
  const [countdown, setCountdown] = useState(null)

  useEffect(() => {
    startCamera()
    return () => stopCamera()
  }, [])

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "user",
          width: { ideal: 1280 },
          height: { ideal: 720 },
        }
      })
      streamRef.current = stream

      const track = stream.getVideoTracks()[0]
      const capabilities = track.getCapabilities?.()
      if (capabilities?.zoom) {
        await track.applyConstraints({ advanced: [{ zoom: capabilities.zoom.min }] })
      }

      if (videoRef.current) {
        videoRef.current.srcObject = stream
        videoRef.current.onloadedmetadata = () => setReady(true)
      }
    } catch (err) {
      setError("Kamera erişimi sağlanamadı. Lütfen izin verin.")
    }
  }

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
    }
  }

  const startCountdown = () => {
    let count = 5
    setCountdown(count)
    const interval = setInterval(() => {
      count -= 1
      if (count === 0) {
        clearInterval(interval)
        setCountdown(null)
        capturePhoto()
      } else {
        setCountdown(count)
      }
    }, 1000)
  }

  const capturePhoto = () => {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas) return

    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext("2d")
    ctx.drawImage(video, 0, 0)

    canvas.toBlob(blob => {
      const url = URL.createObjectURL(blob)
      setCaptured({ blob, url })
      stopCamera()
    }, "image/jpeg", 0.95)
  }

  const confirmPhoto = () => {
    if (captured) {
      const file = new File([captured.blob], "camera_capture.jpg", { type: "image/jpeg" })
      onCapture(file)
      onClose()
    }
  }

  const retake = () => {
    setCaptured(null)
    setCountdown(null)
    startCamera()
  }

  return (
    <div className="fixed inset-0 bg-black z-50 flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 bg-gray-900">
        <button onClick={onClose} className="text-gray-400 hover:text-white text-sm">✕ Kapat</button>
        <h2 className="text-white font-semibold">Fotoğraf Çek</h2>
        <div className="w-16" />
      </div>

      {error && (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-red-400 text-center px-6">{error}</p>
        </div>
      )}

      {!error && (
        <div className="flex-1 relative overflow-hidden">
          {!captured ? (
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
              style={{ transform: "scaleX(-1)" }}
            />
          ) : (
            <img
              src={captured.url}
              alt="captured"
              className="w-full h-full object-cover"
              style={{ transform: "scaleX(-1)" }}
            />
          )}

          {!captured && ready && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <svg viewBox="0 0 200 400" className="h-3/5 opacity-30">
                <ellipse cx="100" cy="45" rx="28" ry="35" fill="none" stroke="white" strokeWidth="2" />
                <rect x="88" y="78" width="24" height="20" fill="none" stroke="white" strokeWidth="2" />
                <path d="M60 98 L140 98 L150 220 L50 220 Z" fill="none" stroke="white" strokeWidth="2" />
                <path d="M60 98 L30 180 L40 185 L68 108" fill="none" stroke="white" strokeWidth="2" />
                <path d="M140 98 L170 180 L160 185 L132 108" fill="none" stroke="white" strokeWidth="2" />
                <path d="M75 220 L65 360 L85 360 L95 220" fill="none" stroke="white" strokeWidth="2" />
                <path d="M125 220 L135 360 L115 360 L105 220" fill="none" stroke="white" strokeWidth="2" />
              </svg>

              {countdown !== null && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-white font-bold" style={{ fontSize: "120px", opacity: 0.9 }}>
                    {countdown}
                  </span>
                </div>
              )}

              <p className="absolute bottom-8 text-white text-sm text-center px-4 opacity-70">
                {countdown !== null
                  ? "Hazır olun!"
                  : "Silüetle hizalanın, tam boy durduğunuzdan emin olun"}
              </p>
            </div>
          )}
        </div>
      )}

      <canvas ref={canvasRef} className="hidden" />

      <div className="px-6 py-4 bg-gray-900 flex gap-3">
        {!captured ? (
          <button
            onClick={startCountdown}
            disabled={!ready || countdown !== null}
            className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold py-3 rounded-xl transition text-center"
          >
            {countdown !== null ? `${countdown} saniye...` : ready ? "📸 Fotoğraf Çek (5sn)" : "Kamera hazırlanıyor..."}
          </button>
        ) : (
          <>
            <button
              onClick={retake}
              className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-semibold py-3 rounded-xl transition"
            >
              Tekrar Çek
            </button>
            <button
              onClick={confirmPhoto}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-xl transition"
            >
              Kullan ✓
            </button>
          </>
        )}
      </div>
    </div>
  )
}