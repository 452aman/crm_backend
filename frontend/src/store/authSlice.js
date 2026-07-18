import { createSlice } from '@reduxjs/toolkit'

const tokenFromStorage = localStorage.getItem('crm_token')
const userFromStorage = localStorage.getItem('crm_user')

const initialState = {
  token: tokenFromStorage || null,
  user: userFromStorage ? JSON.parse(userFromStorage) : null,
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials: (state, action) => {
      const { token, user } = action.payload
      state.token = token
      state.user = user
      localStorage.setItem('crm_token', token)
      localStorage.setItem('crm_user', JSON.stringify(user))
    },
    logout: (state) => {
      state.token = null
      state.user = null
      localStorage.removeItem('crm_token')
      localStorage.removeItem('crm_user')
    },
  },
})

export const { setCredentials, logout } = authSlice.actions
export default authSlice.reducer
