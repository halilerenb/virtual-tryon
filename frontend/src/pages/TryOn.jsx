import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import axios from "axios"

const API = "http://localhost:8000"

const CATEGORIES = [
  { value: "upper", label: "👕 Üst Giyim", desc: "T-shirt, gömlek, kazak" },
  { value: "lower", label: "👖 Alt Giyim", desc: "Pantolon, etek, şort" },
  { value: "outer", label: "🧥 Dış Giyim", desc: "Mont, ceket, kaban" },
  { value: "dress", label: "👗 Elbise", desc: "Elbise, tulum" },
]

export default function TryOn() {
  const { token } = useAuth()
  const navigate = useNavigate()

  const [step, setStep] = useState(1)
  const [category, setCategory] = useState("")
  const [productUrl, setProductUrl] = useState("")
  const [scrapedVariants, setScrapedVariants] = useState([])
  const [selectedVariant, setSelectedVariant] = useState(null)
  const [garmentFile, setGarmentFile] = useState(null)
  const [personFile, setPersonFile] = useState(null)
  const [result, setResult] = useState(null)
  const [scraping, setScraping] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [scrapeError, setScrapeError] = useState("")

  const handleScrape = async () => {
    if (!productUrl) return
    setScraping(true)
    setScrapeError("")
    setScrapedVariants([])
    setSelectedVariant(null)

    try {
      const res = await axios.post(`${API}/pipeline/scrape`, {
        product_url: productUrl
      })
      if (res.data.success && res.data.variants.length > 0) {
        setScrapedVariants(res.data.variants)
      } else {
        setScrapeError("Görsel bulunamadı. Manuel yüklemeyi deneyin.")
      }
    } catch {
      setScrapeError("URL'den görsel çekilemedi. Manuel yüklemeyi deneyin.")
    } finally {
      setScraping(false)
    }
  }

  const handleFileUpload = async () => {
    const garment = selectedVariant || garmentFile
    if (!garment || !personFile) {
      setError("Lütfen hem kıyafet hem de kişi fotoğrafı seçin")
      return
    }

    setLoading(true)
    setError("")

    try {
      let garmentFormData = new FormData()

      if (selectedVariant) {
        const imgRes = await fetch(selectedVariant.image_url)
        const blob = await imgRes.blob()
        const file = new File([blob], "garment.jpg", { type: "image/jpeg" })
        garmentFormData.append("file", file)
      } else {
        garmentFormData.append("file", garmentFile)
      }

      const segRes = await axios.post(`${API}/pipeline/segment`, garmentFormData)

      const personForm = new FormData()
      personForm.append("file", personFile)
      const poseRes = await axios.post(`${API}/pipeline/pose`, personForm)

      setResult({
        segmentation: segRes.data,
        pose: poseRes.data,
        status: "processed"
      })
      setStep(4)
    } catch (err) {
      setError("İşlem sırasında hata oluştu: " + (err.response?.data?.detail || err.message))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <nav className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex justify-between items-center">
        <button onClick={() => navigate("/dashboard")} className="text-gray-400 hover:text-white text-sm">← Geri</button>
        <h1 className="text-xl font-bold">Kıyafet Dene</h1>
        <div className="w-16" />
      </nav>

      <div className="max-w-2xl mx-auto px-6 py-6">
        <div className="flex items-center gap-2 mb-8">
          {[1, 2, 3, 4].map(s => (
            <div key={s} className="flex items-center gap-2 flex-1">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${step >= s ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-500"}`}>{s}</div>
              {s < 4 && <div className={`flex-1 h-0.5 ${step > s ? "bg-blue-600" : "bg-gray-800"}`} />}
            </div>
          ))}
        </div>

        {step === 1 && (
          <div>
            <h2 className="text-xl font-semibold mb-2">Kıyafet kategorisi seç</h2>
            <p className="text-gray-400 text-sm mb-6">Denemek istediğin kıyafet türünü belirt</p>
            <div className="grid grid-cols-2 gap-4">
              {CATEGORIES.map(cat => (
                <button key={cat.value} onClick={() => { setCategory(cat.value); setStep(2) }}
                  className="bg-gray-900 border border-gray-700 hover:border-blue-500 rounded-2xl p-6 text-left transition">
                  <p className="text-2xl mb-2">{cat.label.split(" ")[0]}</p>
                  <p className="font-semibold">{cat.label.split(" ").slice(1).join(" ")}</p>
                  <p className="text-gray-400 text-sm mt-1">{cat.desc}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {step === 2 && (
          <div>
            <h2 className="text-xl font-semibold mb-2">Kıyafet görseli</h2>
            <p className="text-gray-400 text-sm mb-6">Ürün URL'si gir veya görsel yükle</p>

            <div className="space-y-4">
              <div>
                <label className="text-sm text-gray-400 mb-1 block">Ürün URL'si</label>
                <div className="flex gap-2">
                  <input
                    type="url"
                    value={productUrl}
                    onChange={e => setProductUrl(e.target.value)}
                    className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-blue-500"
                    placeholder="https://www.trendyol.com/urun/..."
                  />
                  <button
                    onClick={handleScrape}
                    disabled={!productUrl || scraping}
                    className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-3 rounded-lg text-sm font-semibold transition whitespace-nowrap"
                  >
                    {scraping ? "Çekiliyor..." : "Görselleri Getir"}
                  </button>
                </div>
                {scrapeError && <p className="text-red-400 text-sm mt-2">{scrapeError}</p>}
              </div>

              {scrapedVariants.length > 0 && (
                <div>
                  <p className="text-sm text-gray-400 mb-2">{scrapedVariants.length} görsel bulundu — hangisini denemek istiyorsun?</p>
                  <div className="grid grid-cols-3 gap-3">
                    {scrapedVariants.map((v, i) => (
                      <button
                        key={i}
                        onClick={() => setSelectedVariant(v)}
                        className={`relative rounded-xl overflow-hidden border-2 transition ${selectedVariant?.image_url === v.image_url ? "border-blue-500" : "border-gray-700 hover:border-gray-500"}`}
                      >
                        <img
                          src={v.image_url}
                          alt={v.color}
                          className="w-full h-32 object-cover"
                          onError={e => e.target.style.display = 'none'}
                        />
                        {selectedVariant?.image_url === v.image_url && (
                          <div className="absolute top-1 right-1 bg-blue-600 rounded-full w-5 h-5 flex items-center justify-center text-xs">✓</div>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="text-center text-gray-600 text-sm">— veya görsel yükle —</div>

              <div>
                <input
                  type="file"
                  accept="image/*"
                  onChange={e => { setGarmentFile(e.target.files[0]); setSelectedVariant(null) }}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-gray-400 file:mr-4 file:py-1 file:px-4 file:rounded file:border-0 file:text-sm file:bg-blue-600 file:text-white"
                />
              </div>

              {garmentFile && !selectedVariant && (
                <img src={URL.createObjectURL(garmentFile)} alt="garment"
                  className="w-48 h-48 object-contain rounded-xl border border-gray-700 mx-auto" />
              )}
            </div>

            <div className="flex gap-3 mt-6">
              <button onClick={() => setStep(1)} className="text-gray-400 hover:text-white px-4 py-2 text-sm">← Geri</button>
              <button
                onClick={() => setStep(3)}
                disabled={!selectedVariant && !garmentFile}
                className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold py-3 rounded-xl transition"
              >
                Devam →
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div>
            <h2 className="text-xl font-semibold mb-2">Fotoğrafın</h2>
            <p className="text-gray-400 text-sm mb-6">Önden çekilmiş, tam boy bir fotoğraf yükle</p>

            <input
              type="file"
              accept="image/*"
              onChange={e => setPersonFile(e.target.files[0])}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-gray-400 file:mr-4 file:py-1 file:px-4 file:rounded file:border-0 file:text-sm file:bg-blue-600 file:text-white"
            />

            {personFile && (
              <img src={URL.createObjectURL(personFile)} alt="person"
                className="w-48 h-64 object-cover rounded-xl border border-gray-700 mx-auto mt-4" />
            )}

            {error && <p className="text-red-400 text-sm mt-4">{error}</p>}

            <div className="flex gap-3 mt-6">
              <button onClick={() => setStep(2)} className="text-gray-400 hover:text-white px-4 py-2 text-sm">← Geri</button>
              <button
                onClick={handleFileUpload}
                disabled={!personFile || loading}
                className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold py-3 rounded-xl transition"
              >
                {loading ? "İşleniyor..." : "Denemeyi Başlat →"}
              </button>
            </div>
          </div>
        )}

        {step === 4 && result && (
          <div>
            <h2 className="text-xl font-semibold mb-2">İşlem Tamamlandı</h2>
            <p className="text-gray-400 text-sm mb-6">Pose ve segmentasyon başarıyla tamamlandı.</p>

            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-400">Keypoint sayısı</span>
                <span className="text-white font-semibold">{result.pose.keypoint_count}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Kıyafet kapsama</span>
                <span className="text-white font-semibold">%{result.segmentation.mask_coverage_percent}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Kategori</span>
                <span className="text-white font-semibold">{category}</span>
              </div>
            </div>

            <div className="bg-blue-900/30 border border-blue-700/50 rounded-2xl p-4 mt-4">
              <p className="text-blue-300 text-sm">
                🚀 Try-on modeli entegrasyonu yakında eklenecek.
              </p>
            </div>

            <button
              onClick={() => { setStep(1); setResult(null); setPersonFile(null); setGarmentFile(null); setScrapedVariants([]); setSelectedVariant(null) }}
              className="w-full mt-4 bg-gray-800 hover:bg-gray-700 text-white font-semibold py-3 rounded-xl transition"
            >
              Yeni Deneme
            </button>
          </div>
        )}
      </div>
    </div>
  )
}