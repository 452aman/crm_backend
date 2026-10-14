import { createApi, fetchBaseQuery, type BaseQueryFn, type FetchArgs, type FetchBaseQueryError } from '@reduxjs/toolkit/query/react'
import type { Action, AtRisk, FollowUp, HCP, HCPDetail, Interaction, Overview, Page, Parsed, Product, TeamRow, User } from '../types'
import { clear, setTokens } from './auth'

interface Tokens { access_token: string; refresh_token: string }
type RootLike = { auth: { access: string | null; refresh: string | null } }

const raw = fetchBaseQuery({
  baseUrl: '/api/v1',
  prepareHeaders: (h, { getState }) => { const t = (getState() as RootLike).auth.access; if (t) h.set('Authorization', `Bearer ${t}`); return h },
})

// On a 401, exchange the refresh token once (shared by concurrent requests) and replay the request.
let refreshing: Promise<boolean> | null = null
const withReauth: BaseQueryFn<string | FetchArgs, unknown, FetchBaseQueryError> = async (args, api, extra) => {
  let res = await raw(args, api, extra)
  const url = typeof args === 'string' ? args : args.url
  if (res.error?.status === 401 && !url.startsWith('/auth/')) {
    const refresh = (api.getState() as RootLike).auth.refresh
    if (refresh) {
      refreshing ??= (async () => {
        const r = await raw({ url: '/auth/refresh', method: 'POST', body: { refresh_token: refresh } }, api, extra)
        if (r.data) { const t = r.data as Tokens; api.dispatch(setTokens({ access: t.access_token, refresh: t.refresh_token })); return true }
        api.dispatch(clear()); return false
      })().finally(() => { refreshing = null })
      if (await refreshing) res = await raw(args, api, extra)
    }
  }
  return res
}

export const api = createApi({
  reducerPath: 'api', baseQuery: withReauth,
  tagTypes: ['Me', 'HCP', 'Interaction', 'FollowUp', 'Stats', 'Chat'],
  endpoints: (b) => ({
    login: b.mutation<Tokens, { email: string; password: string }>({
      query: ({ email, password }) => ({ url: '/auth/login', method: 'POST', body: new URLSearchParams({ username: email, password }) }),
    }),
    signup: b.mutation<User, { name: string; email: string; password: string; role: string }>({ query: (body) => ({ url: '/auth/signup', method: 'POST', body }) }),
    me: b.query<User, void>({ query: () => '/auth/me', providesTags: ['Me'] }),
    reps: b.query<User[], void>({ query: () => '/auth/reps' }),
    products: b.query<Product[], void>({ query: () => '/products' }),
    specialties: b.query<string[], void>({ query: () => '/hcps/specialties' }),
    hcps: b.query<Page<HCP>, Record<string, unknown>>({ query: (params) => ({ url: '/hcps', params }), providesTags: ['HCP'] }),
    hcp: b.query<HCPDetail, number>({ query: (id) => `/hcps/${id}`, providesTags: ['HCP', 'Interaction', 'FollowUp'] }),
    interactions: b.query<Page<Interaction>, Record<string, unknown>>({ query: (params) => ({ url: '/interactions', params }), providesTags: ['Interaction'] }),
    parseNote: b.mutation<Parsed, string>({ query: (text) => ({ url: '/interactions/parse', method: 'POST', body: { text } }) }),
    createInteraction: b.mutation<Interaction, Record<string, unknown>>({
      query: (body) => ({ url: '/interactions', method: 'POST', body }), invalidatesTags: ['Interaction', 'FollowUp', 'Stats', 'HCP'],
    }),
    deleteInteraction: b.mutation<void, number>({ query: (id) => ({ url: `/interactions/${id}`, method: 'DELETE' }), invalidatesTags: ['Interaction', 'Stats', 'HCP'] }),
    followups: b.query<FollowUp[], void>({ query: () => '/followups', providesTags: ['FollowUp'] }),
    doneFollowup: b.mutation<FollowUp, { id: number; done: boolean }>({
      query: ({ id, done }) => ({ url: `/followups/${id}`, method: 'PATCH', body: { done } }), invalidatesTags: ['FollowUp', 'Stats'],
    }),
    overview: b.query<Overview, { days: number; rep_id?: number }>({ query: (params) => ({ url: '/analytics/overview', params }), providesTags: ['Stats', 'Interaction'] }),
    atRisk: b.query<AtRisk[], { rep_id?: number } | void>({ query: (params) => ({ url: '/analytics/at-risk', params: params ?? undefined }), providesTags: ['Stats', 'Interaction'] }),
    team: b.query<TeamRow[], number>({ query: (days) => ({ url: '/analytics/team', params: { days } }), providesTags: ['Stats', 'Interaction'] }),
    chatHistory: b.query<{ id: number; role: 'user' | 'assistant'; content: string; trace: never[]; actions: Action[] }[], void>({ query: () => '/chat/history', providesTags: ['Chat'] }),
    clearChat: b.mutation<void, void>({ query: () => ({ url: '/chat/history', method: 'DELETE' }), invalidatesTags: ['Chat'] }),
    confirmAction: b.mutation<Action, number>({ query: (id) => ({ url: `/chat/actions/${id}/confirm`, method: 'POST' }), invalidatesTags: ['Interaction', 'FollowUp', 'Stats', 'HCP', 'Chat'] }),
    cancelAction: b.mutation<Action, number>({ query: (id) => ({ url: `/chat/actions/${id}/cancel`, method: 'POST' }), invalidatesTags: ['Chat'] }),
  }),
})

export const {
  useLoginMutation, useSignupMutation, useMeQuery, useRepsQuery, useProductsQuery, useSpecialtiesQuery, useHcpsQuery, useHcpQuery,
  useInteractionsQuery, useParseNoteMutation, useCreateInteractionMutation, useDeleteInteractionMutation, useFollowupsQuery,
  useDoneFollowupMutation, useOverviewQuery, useAtRiskQuery, useTeamQuery, useChatHistoryQuery, useClearChatMutation,
  useConfirmActionMutation, useCancelActionMutation,
} = api
