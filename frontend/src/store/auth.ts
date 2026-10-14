import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

const load = (k: string) => { try { return localStorage.getItem(k) } catch { return null } }
const save = (k: string, v: string | null) => { try { v ? localStorage.setItem(k, v) : localStorage.removeItem(k) } catch { /* private mode */ } }

interface AuthState { access: string | null; refresh: string | null }
const initial: AuthState = { access: load('crm_access'), refresh: load('crm_refresh') }

const slice = createSlice({
  name: 'auth', initialState: initial,
  reducers: {
    setTokens(s, a: PayloadAction<{ access: string; refresh: string }>) {
      s.access = a.payload.access; s.refresh = a.payload.refresh
      save('crm_access', s.access); save('crm_refresh', s.refresh)
    },
    clear(s) { s.access = null; s.refresh = null; save('crm_access', null); save('crm_refresh', null) },
  },
})
export const { setTokens, clear } = slice.actions
export default slice.reducer
