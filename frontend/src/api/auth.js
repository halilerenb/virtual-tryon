import axios from 'axios'

const API = 'http://localhost:8000'

export const register = async (email, password, fullName) => {
  const res = await axios.post(`${API}/users/register`, {
    email,
    password,
    full_name: fullName
  })
  return res.data
}

export const login = async (email, password) => {
  const formData = new FormData()
  formData.append('username', email)
  formData.append('password', password)
  const res = await axios.post(`${API}/users/login`, formData)
  return res.data
}

export const getMe = async (token) => {
  const res = await axios.get(`${API}/users/me`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export const saveMeasurements = async (token, data) => {
  const res = await axios.post(`${API}/users/measurements`, data, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export const getMeasurements = async (token) => {
  const res = await axios.get(`${API}/users/measurements`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}