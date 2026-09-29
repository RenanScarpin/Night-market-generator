export type MarketMode = 'core_raw' | 'expanded_2045'
export type GmChoiceBehavior = 'random' | 'leave'

export interface MarketGenerateRequest {
  mode: MarketMode
  seed?: number | null
  gm_choice: GmChoiceBehavior
}

export interface MarketItem {
  item_id: number
  name: string
  slug: string
  info: string
  item_kind: string
  prices: string[]
  manufacturers: string[]
  primary_source: string | null
  primary_page: number | null
  tags: string[]
}

export interface StockSlot {
  stock_roll_id: number
  category_code: string
  category_name: string
  d100_roll: number
  d100_min: number
  d100_max: number
  raw_result: string
  raw_cost: string | null
  resolution_mode: 'static' | 'exact_item' | 'query' | 'gm_choice' | string
  selector: Record<string, unknown>
  selected_item: MarketItem | null
  supplemental_items: MarketItem[]
  supplemental_reason: string | null
}

export interface MarketSection {
  category_roll: number
  category_code: string
  category_name: string
  description: string
  stock_count_roll: number
  stock_roll_attempts: number[]
  slots: StockSlot[]
}

export interface NightMarket {
  generator_version: string
  seed: number
  mode: MarketMode
  gm_choice_behavior: GmChoiceBehavior
  category_roll_attempts: number[]
  sections: MarketSection[]
}

export interface ItemPriceDetail {
  item_price_id: number
  variant_label: string | null
  price_kind: string
  cost_eb: number | null
  price_category: string | null
  unit: string
  unit_quantity: number
  cost_basis: string | null
  source_price_text: string | null
  notes: string | null
}

export interface CategoryDetail {
  category_id: number
  parent_category_id: number | null
  name: string
  slug: string
  sort_order: number | null
  is_primary?: boolean | null
  item_count?: number | null
}

export interface CompanyDetail {
  company_id: number
  name: string
  role: string
}

export interface AliasDetail {
  alias: string
  alias_type: string
}

export interface MarketTagDetail {
  tag_id: number
  code: string
  name: string
  tag_group: string
  description: string | null
  origin?: string | null
  notes?: string | null
  item_count?: number | null
}

export interface SourceDetail {
  source_id: number
  code: string
  title: string
  version: string | null
  publication_date: string | null
  source_role: string
  source_name: string | null
  printed_page: number | null
  pdf_page: number | null
  section: string | null
  notes: string | null
}

export interface RelationshipDetail {
  relation_type: string
  target_item_id: number
  target_name: string
  target_slug: string
  notes: string | null
}

export interface EligibilityDetail {
  profile_code: string
  profile_name: string
  status: string
  reason: string | null
}

export interface ItemDetail {
  item_id: number
  canonical_name: string
  slug: string
  info: string
  mechanics: Record<string, unknown> | null
  item_kind: string
  record_status: string
  needs_review: boolean
  review_note: string | null
  canon_2045: boolean
  prices: ItemPriceDetail[]
  categories: CategoryDetail[]
  companies: CompanyDetail[]
  aliases: AliasDetail[]
  tags: MarketTagDetail[]
  sources: SourceDetail[]
  relationships: RelationshipDetail[]
  eligibility: EligibilityDetail[]
}

export interface ApiErrorBody {
  detail?: string | Array<Record<string, unknown>>
}
