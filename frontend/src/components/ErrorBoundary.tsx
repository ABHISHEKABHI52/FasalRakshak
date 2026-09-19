"use client";

/**
 * Reusable error boundary for feature trees (docs/05 §1.3, docs/39).
 * Route-level failures are additionally handled by app/error.tsx.
 */

import { Component, type ErrorInfo, type ReactNode } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  override state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    // Client-side observability hook (docs/00 §34 — wire to Sentry in a later phase).
    console.error("FasalRakshak UI error boundary:", error.message, info.componentStack);
  }

  override render(): ReactNode {
    if (this.state.hasError) {
      return (
        this.props.fallback ?? (
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">
            <p className="font-medium">Something went wrong in this section.</p>
            <p className="mt-1">Your data is safe. Please reload the page and try again.</p>
          </div>
        )
      );
    }
    return this.props.children;
  }
}