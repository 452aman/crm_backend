export type Tier = 'A' | 'B' | 'C'
export type Sentiment = 'positive' | 'neutral' | 'negative'
export type ITypeName = 'visit' | 'call' | 'email' | 'conference' | 'sample_drop'
export const INTERACTION_TYPES: ITypeName[] = ['visit', 'call', 'email', 'conference', 'sample_drop']

export interface User { id: number; name: string; email: string; role: 'rep' | 'manager' }
export interface HCP { id: number; name: string; specialty: string; hospital: string; city: string; tier: Tier; assigned_rep_id: number | null; last_contact: string | null; interaction_count: number }
export interface Product { id: number; name: string; category: string }
export interface Interaction {
  id: number; occurred_on: string; type: ITypeName; location: string; notes: string; summary: string; sentiment: Sentiment
  next_steps: string; source: string; hcp: HCP; rep: { id: number; name: string }; products: Product[]
}
export interface Page<T> { items: T[]; total: number; page: number; size: number }
export interface FollowUp { id: number; title: string; due_on: string; done: boolean; overdue: boolean; hcp: HCP }
export interface Overview {
  days: number; interactions: number; unique_hcps: number; positive_rate: number | null; open_followups: number; overdue_followups: number
  tier_a_coverage: number | null; by_type: Record<string, number>; by_sentiment: Record<string, number>
  series: { label: string; count: number }[]; top_products: { name: string; count: number }[]
}
export interface AtRisk { hcp_id: number; name: string; specialty: string; hospital: string; tier: Tier; days_since: number | null; last_sentiment: string | null; suggestion: string }
export interface TeamRow { rep_id: number; name: string; interactions: number; unique_hcps: number; positive_rate: number | null; overdue_followups: number; at_risk_hcps: number }
export interface HCPDetail { hcp: HCP; timeline: Interaction[]; sentiment: Record<string, number>; products: { name: string; count: number }[]; followups: FollowUp[] }
export interface Parsed {
  used_llm: boolean; hcp_id: number | null; hcp_candidates: { id: number; name: string; hospital: string }[]; doctor_name: string | null
  type: ITypeName; location: string; sentiment: Sentiment; product_ids: number[]; product_names: string[]; notes: string
  next_steps: string; follow_up_days: number | null; occurred_on: string
}
export interface Action { id: number; kind: string; payload: Record<string, unknown>; status: 'pending' | 'confirmed' | 'cancelled'; result: Record<string, unknown> }
export interface TraceEv { type: 'tool_call' | 'tool_result'; name: string; args?: Record<string, unknown>; content?: string }
export interface ChatMsg { id?: number; role: 'user' | 'assistant'; content: string; trace?: TraceEv[]; actions?: Action[]; streaming?: boolean; error?: string }
