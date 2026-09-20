/** API contract types — mirrors backend Pydantic schemas (docs/08 §11). */

/** Stable error envelope returned by the backend for every failure. */
export interface ApiErrorEnvelope {
  code: string;
  message_key: string;
  details?: {
    fields?: Array<{ field: string; message: string }>;
    required_roles?: string[];
    retry_after_seconds?: number;
    [key: string]: unknown;
  };
}

export type RoleName = "FARMER" | "EXTENSION_WORKER" | "EXPERT" | "OFFICER" | "ADMIN";

export interface UserDto {
  id: string;
  phone: string;
  email: string | null;
  full_name: string;
  preferred_language: string;
  district: string | null;
  state: string | null;
  consent_ml_use: boolean;
  roles: RoleName[];
  created_at: string;
}

export interface TokenResponseDto {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserDto;
}

export interface RegisterResponseDto {
  user_id: string;
  roles: RoleName[];
}

export interface HealthDto {
  status: string;
  app: string;
}

export interface ReadinessDto {
  db: boolean;
}

/** Farmer Core Loop DTOs (docs/08 §2-§3). */

export interface FarmDto {
  id: string;
  name: string;
  address: string | null;
  district: string | null;
  state: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  field_count: number;
}

export type FarmCreate = {
  name: string;
  address?: string | null;
  district?: string | null;
  state?: string | null;
};

export type FarmUpdate = Omit<Partial<FarmCreate>, "name"> & Pick<FarmCreate, "name">;

export interface FieldDto {
  id: string;
  farm_id: string;
  name: string;
  area_hectares: number | null;
  location: { lat: number; lng: number } | null;
  soil_type: string | null;
  district_code: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  crop_cycle_count: number;
}

export type FieldCreate = {
  farm_id: string;
  name: string;
  area_hectares?: number | null;
  location?: { lat: number; lng: number } | null;
  soil_type?: string | null;
  district_code?: string | null;
};

export type FieldUpdate = Omit<Partial<FieldCreate>, "farm_id">;

export interface CropDto {
  id: string;
  code: string;
  name_en: string;
  name_hi: string;
  scientific_name: string | null;
  is_supported: boolean;
  stage_model: Record<string, number> | null;
}

export type CropStage =
  | "seedling"
  | "vegetative"
  | "flowering"
  | "fruiting"
  | "maturity";
export type CycleStatus = "active" | "completed" | "abandoned";

export interface CropCycleDto {
  id: string;
  field_id: string;
  crop_id: string;
  crop_code: string;
  crop_name_en: string;
  crop_name_hi: string;
  variety: string | null;
  sowing_date: string;
  expected_harvest_date: string | null;
  current_stage: CropStage;
  stage_updated_at: string | null;
  status: CycleStatus;
  created_at: string;
  updated_at: string;
}

export type CropCycleCreate = {
  field_id: string;
  crop_id: string;
  variety?: string | null;
  sowing_date: string;
  expected_harvest_date?: string | null;
};

export type CropCycleUpdate = {
  variety?: string | null;
  expected_harvest_date?: string | null;
  status?: CycleStatus | null;
};

export type PlantPart = "leaf" | "stem" | "fruit" | "whole_plant" | "trap";
export type ScanStatus =
  | "pending_image"
  | "quality_checking"
  | "quality_rejected"
  | "analyzing"
  | "completed"
  | "failed";
export type QualityCategory = "good" | "acceptable" | "poor" | "unusable";

export interface QualityReasonDto {
  code: string;
  message_key: string;
  hint: string;
}

export interface QualitySummaryDto {
  quality_score: number;
  category: QualityCategory;
  usable: boolean;
  leaf_coverage: number | null;
  reasons: QualityReasonDto[];
  metrics: Record<string, number> | null;
  model_ref: string | null;
}

export interface AnalysisSummaryDto {
  status: string;
  primary_label_code: string | null;
  confidence: number | null;
  candidates: Array<{ label_code: string; confidence: number }>;
  reasons: string[];
  model_name: string | null;
  model_version: string | null;
  is_mock: boolean;
  note: string | null;
}

export interface ScanDto {
  id: string;
  client_scan_uuid: string;
  field_id: string;
  crop_cycle_id: string;
  plant_part: PlantPart;
  captured_at: string;
  status: ScanStatus;
  status_reason: string | null;
  created_at: string;
  updated_at: string;
  image: {
    id: string;
    mime_type: string;
    size_bytes: number;
    width: number;
    height: number;
  } | null;
  quality: QualitySummaryDto | null;
  analysis: AnalysisSummaryDto | null;
}

export interface ScanListDto {
  items: ScanDto[];
  next_cursor: string | null;
}

export interface ImageUploadResponseDto {
  scan_id: string;
  image_id: string;
  status: ScanStatus;
  quality: QualitySummaryDto;
  analysis: AnalysisSummaryDto | null;
}

export type ScanCreate = {
  field_id: string;
  crop_cycle_id: string;
  plant_part: PlantPart;
  captured_at: string;
  client_scan_uuid: string;
};