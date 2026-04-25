import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { getMeasurements, saveMeasurements } from "../api/auth"

export default function Dashboard() {
  const { user, token, logoutUser } = useAuth()
  const navigate = useNavigate()
  const [measurements, setMeasurements] = useState(null)
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({
    height_cm: "", weight_kg: "", chest_cm: "",
    waist_cm: "", hip_cm: "", gender: "unisex"
  })
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState("")

  useEffect(() => {
    getMeasurements(token)
      .then(data => {
        if (data.success) {
          setMeasurements(data.measurements)
          setForm(data.measurements)
        }
      })
      .catch(() => {})
  }, [token])

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await saveMeasurements(token, form)
      setMeasurements(form)
      setEditing(false)
      setMessage("Ölçüler kaydedildi!")
      setTimeout(() => setMessage(""), 3000)
    } catch {
      setMessage("Hata oluştu")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Navbar */}
      <nav className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex justify-between items-center">
        <h1 className="text-xl font-bold">Virtual Try-On</h1>
        <div className="flex items-center gap-4">
          <span className="text-gray-400 text-sm">{user?.email}</span>
          <button
            onClick={logoutUser}
            className="text-sm text-red-400 hover:text-red-300"
          >
            Çıkış
          </button>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">

        {/* Hoş geldin */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
          <h2 className="text-xl font-semibold mb-1">
            Hoş geldin, {user?.full_name || user?.email} 👋
          </h2>
          <p className="text-gray-400 text-sm">
            Kıyafet denemesi yapmak için aşağıdan ölçülerini gir, sonra Try-On'a geç.
          </p>
        </div>

        {/* Beden ölçüleri */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">Beden Ölçüleri</h3>
            {!editing && (
              <button
                onClick={() => setEditing(true)}
                className="text-sm text-blue-400 hover:text-blue-300"
              >
                {measurements ? "Düzenle" : "Ekle"}
              </button>
            )}
          </div>

          {message && (
            <p className="text-green-400 text-sm mb-4">{message}</p>
          )}

          {editing ? (
            <form onSubmit={handleSave} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                {[
                  { key: "height_cm", label: "Boy (cm)" },
                  { key: "weight_kg", label: "Kilo (kg)" },
                  { key: "chest_cm", label: "Göğüs (cm)" },
                  { key: "waist_cm", label: "Bel (cm)" },
                  { key: "hip_cm", label: "Kalça (cm)" },
                ].map(({ key, label }) => (
                  <div key={key}>
                    <label className="text-sm text-gray-400 mb-1 block">{label}</label>
                    <input
                      type="number"
                      value={form[key] || ""}
                      onChange={e => setForm({ ...form, [key]: parseFloat(e.target.value) })}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                      placeholder="0"
                    />
                  </div>
                ))}
                <div>
                  <label className="text-sm text-gray-400 mb-1 block">Cinsiyet</label>
                  <select
                    value={form.gender || "unisex"}
                    onChange={e => setForm({ ...form, gender: e.target.value })}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="unisex">Unisex</option>
                    <option value="male">Erkek</option>
                    <option value="female">Kadın</option>
                  </select>
                </div>
              </div>
              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={saving}
                  className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-2 rounded-lg text-sm font-semibold transition"
                >
                  {saving ? "Kaydediliyor..." : "Kaydet"}
                </button>
                <button
                  type="button"
                  onClick={() => setEditing(false)}
                  className="text-gray-400 hover:text-gray-300 px-4 py-2 text-sm"
                >
                  İptal
                </button>
              </div>
            </form>
          ) : measurements ? (
            <div className="grid grid-cols-3 gap-4">
              {[
                { label: "Boy", value: measurements.height_cm, unit: "cm" },
                { label: "Kilo", value: measurements.weight_kg, unit: "kg" },
                { label: "Göğüs", value: measurements.chest_cm, unit: "cm" },
                { label: "Bel", value: measurements.waist_cm, unit: "cm" },
                { label: "Kalça", value: measurements.hip_cm, unit: "cm" },
              ].map(({ label, value, unit }) => (
                <div key={label} className="bg-gray-800 rounded-xl p-4 text-center">
                  <p className="text-gray-400 text-xs mb-1">{label}</p>
                  <p className="text-white font-semibold">{value} {unit}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">
              Henüz ölçü girmediniz. "Ekle" butonuna tıklayın.
            </p>
          )}
        </div>

        {/* Try-On butonu */}
        <button
          onClick={() => navigate("/tryon")}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 rounded-2xl text-lg transition"
        >
          👕 Kıyafet Denemeye Başla
        </button>
      </div>
    </div>
  )
}