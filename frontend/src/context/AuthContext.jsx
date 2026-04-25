import { createContext, useContext, useState, useEffect } from "react"
import { getMe } from "../api/auth"

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem("token"))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (token) {
      getMe(token)
        .then(u => setUser(u))
        .catch(() => {
          setToken(null)
          localStorage.removeItem("token")
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [token])

  const loginUser = (data) => {
    setToken(data.access_token)
    setUser(data.user)
    localStorage.setItem("token", data.access_token)
  }

  const logoutUser = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem("token")
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, loginUser, logoutUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)