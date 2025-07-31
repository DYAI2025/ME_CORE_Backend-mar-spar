"""
Render Environment Variable Utilities

Render provides service URLs as 'host' only (e.g., 'my-service.onrender.com')
This utility helps construct full URLs with https:// prefix.
"""
import os
from typing import Optional, Dict
from urllib.parse import urlparse, urlunparse


def get_full_url_from_host(host: Optional[str], scheme: str = "https") -> Optional[str]:
    """
    Convert a host to a full URL with scheme.
    
    Args:
        host: The hostname (e.g., 'my-service.onrender.com')
        scheme: The URL scheme to use (default: 'https')
    
    Returns:
        Full URL with scheme, or None if host is None
    """
    if not host:
        return None
    
    # Check if host already has a scheme
    if "://" in host:
        return host
    
    # Construct full URL
    return f"{scheme}://{host}"


def get_render_service_url(env_var: str, scheme: str = "https") -> Optional[str]:
    """
    Get a full URL from a Render environment variable that contains only a host.
    
    Args:
        env_var: The environment variable name
        scheme: The URL scheme to use (default: 'https')
    
    Returns:
        Full URL with scheme, or None if env var is not set
    """
    host = os.getenv(env_var)
    return get_full_url_from_host(host, scheme)


def get_render_urls() -> Dict[str, Optional[str]]:
    """
    Get all Render service URLs as full URLs.
    
    Returns:
        Dictionary of service names to their full URLs
    """
    return {
        "frontend": get_render_service_url("FRONTEND_URL"),
        "api": get_render_service_url("NEXT_PUBLIC_API_URL"),
        "nextauth": get_render_service_url("NEXTAUTH_URL"),
        "dashboard": get_render_service_url("DASHBOARD_URL"),
    }


def construct_service_endpoint(base_host: Optional[str], path: str = "", scheme: str = "https") -> Optional[str]:
    """
    Construct a full service endpoint URL.
    
    Args:
        base_host: The base hostname
        path: The path to append (e.g., '/api/health')
        scheme: The URL scheme to use (default: 'https')
    
    Returns:
        Full endpoint URL, or None if base_host is None
    """
    base_url = get_full_url_from_host(base_host, scheme)
    if not base_url:
        return None
    
    # Ensure path starts with /
    if path and not path.startswith("/"):
        path = f"/{path}"
    
    return f"{base_url}{path}"


# Convenience functions for specific services
def get_frontend_url(path: str = "") -> Optional[str]:
    """Get the frontend service URL with optional path."""
    host = os.getenv("FRONTEND_URL")
    return construct_service_endpoint(host, path)


def get_api_url(path: str = "") -> Optional[str]:
    """Get the API service URL with optional path."""
    host = os.getenv("NEXT_PUBLIC_API_URL")
    return construct_service_endpoint(host, path)


def get_dashboard_url(path: str = "") -> Optional[str]:
    """Get the dashboard service URL with optional path."""
    host = os.getenv("DASHBOARD_URL")
    return construct_service_endpoint(host, path)


# Example usage in your application:
if __name__ == "__main__":
    # Get full URLs
    frontend_url = get_frontend_url()  # https://me-core-dashboard.onrender.com
    api_health = get_api_url("/api/health")  # https://me-core-backend.onrender.com/api/health
    
    # Get all URLs
    urls = get_render_urls()
    print(f"Frontend URL: {urls['frontend']}")
    print(f"API URL: {urls['api']}")