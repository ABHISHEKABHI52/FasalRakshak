/**
 * message_key → farmer-facing English text (docs/39).
 * Phase 1 keeps this as a typed map so every new locale file can reuse the keys
 * (i18n loading of locale bundles lands with the farmer flows in Phase 2).
 */

import type { ApiError } from "@/lib/api-client";

const MESSAGES: Record<string, string> = {
  "errors.validation_error": "Please check the highlighted fields.",
  "errors.unauthorized": "Your session has ended. Please sign in again.",
  "errors.forbidden": "You do not have permission for this action.",
  "errors.not_found": "We could not find that item.",
  "errors.conflict": "That already exists.",
  "errors.duplicate_phone": "This phone number is already registered.",
  "errors.invalid_credentials": "Phone number or password is incorrect.",
  "errors.rate_limited": "Too many attempts. Please wait a moment and try again.",
  "errors.service_unavailable": "The service is temporarily unavailable. Please try again.",
  "errors.internal_error": "Something went wrong on our side. Please try again.",
};

export function friendlyMessage(error: unknown): string {
  if (error && typeof error === "object" && "messageKey" in error) {
    const apiError = error as ApiError;
    return MESSAGES[apiError.messageKey] ?? MESSAGES["errors.internal_error"] ?? "Please try again.";
  }
  if (error instanceof Error) {
    return MESSAGES["errors.internal_error"] ?? "Please try again.";
  }
  return "Please try again.";
}