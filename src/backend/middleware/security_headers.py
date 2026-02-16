"""
HTTP Security Headers Middleware

Adds essential HTTP security headers to prevent common web attacks:
- XSS (Cross-Site Scripting)
- Clickjacking
- MIME sniffing attacks
- Man-in-the-middle attacks

References:
- OWASP Secure Headers Project
- Mozilla Web Security Guidelines
- Google Web Fundamentals - Security
"""

from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.core.logging import get_logger
from backend.core.config import settings

logger = get_logger("security_headers")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Security Headers Middleware

    Adds security-related HTTP headers to all responses to enhance application security
    """

    def __init__(
        self,
        app: ASGIApp,
        # X-Frame-Options configuration
        x_frame_options: str = "DENY",  # DENY, SAMEORIGIN, ALLOW-FROM uri
        
        # X-Content-Type-Options configuration
        x_content_type_options: str = "nosniff",
        
        # X-XSS-Protection configuration (deprecated but backward compatible)
        x_xss_protection: str = "1; mode=block",
        
        # Referrer-Policy configuration
        referrer_policy: str = "strict-origin-when-cross-origin",
        
        # Permissions-Policy configuration
        permissions_policy: str = None,
        
        # HSTS (HTTP Strict Transport Security) configuration
        hsts_max_age: int = 31536000,  # 1 year
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = False,  # Enable carefully, requires submission to browser vendors
        
        # Content-Security-Policy configuration
        csp_directives: dict = None,
        csp_report_only: bool = False,  # True = report only, don't block
        csp_report_uri: str = None,
        
        # Development environment option
        disable_in_dev: bool = True,  # Disable some strict policies in development
    ):
        super().__init__(app)
        
        self.x_frame_options = x_frame_options
        self.x_content_type_options = x_content_type_options
        self.x_xss_protection = x_xss_protection
        self.referrer_policy = referrer_policy
        self.permissions_policy = permissions_policy
        
        # HSTS configuration
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        
        # CSP configuration
        self.csp_directives = csp_directives or self._get_default_csp_directives()
        self.csp_report_only = csp_report_only
        self.csp_report_uri = csp_report_uri
        
        self.disable_in_dev = disable_in_dev
        
        # Adjust configuration based on environment
        self._adjust_for_environment()
    
    def _get_default_csp_directives(self) -> dict:
        """Get default CSP directives"""
        return {
            "default-src": ["'self'"],
            "script-src": ["'self'", "'unsafe-inline'"],  # Allow inline scripts (Vue needs this)
            "style-src": ["'self'", "'unsafe-inline'"],  # Allow inline styles
            "img-src": ["'self'", "data:", "blob:"],
            "font-src": ["'self'"],
            "connect-src": ["'self'"],
            "media-src": ["'self'"],
            "object-src": ["'none'"],  # Disable Flash and other plugins
            "frame-ancestors": ["'none'"],  # Equivalent to X-Frame-Options: DENY
            "base-uri": ["'self'"],
            "form-action": ["'self'"],
        }
    
    def _adjust_for_environment(self):
        """Adjust security configuration based on environment"""
        if settings.ENVIRONMENT == "development" and self.disable_in_dev:
            # Development environment: relax some restrictions
            logger.info("🔧 Development mode: Some security headers relaxed for debugging")
            
            # Allow more CSP sources (like Vue DevTools)
            self.csp_directives["script-src"].extend([
                "'unsafe-eval'",  # Allow eval (development needs this)
            ])
            
            # Disable HSTS in development (avoid HTTPS redirect issues)
            self.hsts_max_age = 0
        
        elif settings.ENVIRONMENT == "production":
            # Production environment: enable strictest configuration
            logger.info("🔒 Production mode: Maximum security headers enabled")
            
            # Enable HSTS preload (use with caution)
            if self.hsts_preload:
                self.hsts_max_age = 63072000  # 2 years
    
    def _build_csp_header(self) -> str:
        """Build CSP header value"""
        directives = []
        for directive, sources in self.csp_directives.items():
            if sources:
                directives.append(f"{directive} {' '.join(sources)}")
        return "; ".join(directives)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add security headers"""
        
        # Continue processing request
        response = await call_next(request)
        
        # Add security headers
        
        # 1. X-Content-Type-Options: Prevent MIME sniffing attacks
        if self.x_content_type_options:
            response.headers["X-Content-Type-Options"] = self.x_content_type_options
        
        # 2. X-Frame-Options: Prevent clickjacking
        if self.x_frame_options:
            response.headers["X-Frame-Options"] = self.x_frame_options
        
        # 3. X-XSS-Protection: Browser's XSS filter (backward compatible)
        if self.x_xss_protection:
            response.headers["X-XSS-Protection"] = self.x_xss_protection
        
        # 4. Referrer-Policy: Control Referrer information leakage
        if self.referrer_policy:
            response.headers["Referrer-Policy"] = self.referrer_policy
        
        # 5. Permissions-Policy: Control browser feature permissions
        if self.permissions_policy:
            response.headers["Permissions-Policy"] = self.permissions_policy
        
        # 6. Strict-Transport-Security (HSTS): Force HTTPS
        if self.hsts_max_age > 0:
            hsts_value = f"max-age={self.hsts_max_age}"
            if self.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.hsts_preload:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value
        
        # 7. Content-Security-Policy (CSP): Content security policy
        csp_header = "Content-Security-Policy"
        if self.csp_report_only:
            csp_header = "Content-Security-Policy-Report-Only"
        
        csp_value = self._build_csp_header()
        if csp_value:
            response.headers[csp_header] = csp_value
            
            # Add report URI if configured
            if self.csp_report_uri:
                response.headers[csp_header] += f"; report-uri {self.csp_report_uri}"
        
        # 8. Additional security headers
        # Remove Server header (avoid leaking server information)
        if "Server" in response.headers:
            del response.headers["Server"]
        
        # Add X-Download-Options (IE download option)
        response.headers["X-Download-Options"] = "noopen"
        
        return response


class SimpleSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Simplified security headers middleware (adds basic security headers only)
    
    For scenarios where full security header configuration is not needed
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Basic security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
