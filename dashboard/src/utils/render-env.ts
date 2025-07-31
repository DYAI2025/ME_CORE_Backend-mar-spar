/**
 * Render environment utilities for handling host-only environment variables.
 * 
 * Render provides host-only values (e.g., 'example.onrender.com') for service URLs.
 * This module provides utilities to construct full URLs from these hosts.
 */

/**
 * Convert a host-only value to a full URL.
 * 
 * @param host - The host value (e.g., 'example.onrender.com')
 * @param defaultScheme - The scheme to use (default: 'https')
 * @returns Full URL (e.g., 'https://example.onrender.com') or null if host is null/empty
 */
export function getFullUrlFromHost(host: string | null | undefined, defaultScheme: string = 'https'): string | null {
  if (!host) {
    return null;
  }
  
  // If it already has a scheme, return as-is
  if (host.startsWith('http://') || host.startsWith('https://')) {
    return host;
  }
  
  // Add the scheme
  return `${defaultScheme}://${host}`;
}

/**
 * Get a full URL from a Render host environment variable.
 * 
 * @param envVarName - Name of the environment variable containing the host
 * @param defaultScheme - The scheme to use (default: 'https')
 * @returns Full URL or null if environment variable is not set
 */
export function getRenderServiceUrl(envVarName: string, defaultScheme: string = 'https'): string | null {
  const host = process.env[envVarName];
  return getFullUrlFromHost(host, defaultScheme);
}

/**
 * Get all Render service URLs from environment variables.
 * 
 * @returns Object containing service names mapped to full URLs
 */
export function getRenderUrls() {
  return {
    backend: getRenderServiceUrl('NEXT_PUBLIC_RENDER_BACKEND_HOST'),
    markerEngine: getRenderServiceUrl('NEXT_PUBLIC_RENDER_MARKER_ENGINE_HOST'),
    dashboard: getRenderServiceUrl('NEXT_PUBLIC_RENDER_DASHBOARD_HOST'),
    repairService: getRenderServiceUrl('NEXT_PUBLIC_RENDER_REPAIR_SERVICE_HOST'),
  };
}

/**
 * Construct a full service endpoint URL with path.
 * 
 * @param serviceHostEnv - Environment variable name containing the host
 * @param path - Path to append to the URL (should start with /)
 * @param defaultScheme - The scheme to use (default: 'https')
 * @returns Full URL with path or null if host is not set
 */
export function constructServiceEndpoint(
  serviceHostEnv: string, 
  path: string = '', 
  defaultScheme: string = 'https'
): string | null {
  const baseUrl = getRenderServiceUrl(serviceHostEnv, defaultScheme);
  if (!baseUrl) {
    return null;
  }
  
  // Ensure path starts with /
  if (path && !path.startsWith('/')) {
    path = `/${path}`;
  }
  
  return `${baseUrl}${path}`;
}

// Convenience functions for specific services
export function getBackendUrl(path: string = ''): string | null {
  return constructServiceEndpoint('NEXT_PUBLIC_RENDER_BACKEND_HOST', path);
}

export function getMarkerEngineUrl(path: string = ''): string | null {
  return constructServiceEndpoint('NEXT_PUBLIC_RENDER_MARKER_ENGINE_HOST', path);
}

export function getDashboardUrl(path: string = ''): string | null {
  return constructServiceEndpoint('NEXT_PUBLIC_RENDER_DASHBOARD_HOST', path);
}

export function getRepairServiceUrl(path: string = ''): string | null {
  return constructServiceEndpoint('NEXT_PUBLIC_RENDER_REPAIR_SERVICE_HOST', path);
}

// For backward compatibility with existing code
export function getServiceUrl(serviceName: 'backend' | 'markerEngine' | 'dashboard' | 'repairService'): string | null {
  const urlGetters = {
    backend: getBackendUrl,
    markerEngine: getMarkerEngineUrl,
    dashboard: getDashboardUrl,
    repairService: getRepairServiceUrl,
  };
  
  const getter = urlGetters[serviceName];
  return getter ? getter() : null;
}

// Type definitions for service URLs
export interface RenderServiceUrls {
  backend: string | null;
  markerEngine: string | null;
  dashboard: string | null;
  repairService: string | null;
}

// Helper to get non-null URLs (throws if any required service is missing)
export function getRequiredRenderUrls(): Required<RenderServiceUrls> {
  const urls = getRenderUrls();
  
  for (const [service, url] of Object.entries(urls)) {
    if (!url) {
      throw new Error(`Missing required Render service URL for ${service}. Please set NEXT_PUBLIC_RENDER_${service.toUpperCase()}_HOST environment variable.`);
    }
  }
  
  return urls as Required<RenderServiceUrls>;
}

// Helper to validate all required URLs are present
export function validateRenderUrls(): boolean {
  const urls = getRenderUrls();
  return Object.values(urls).every(url => url !== null);
}

// Export a default instance with all URLs
export const renderUrls = getRenderUrls();