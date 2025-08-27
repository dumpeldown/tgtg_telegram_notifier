#!/usr/bin/env python3
"""
TGTG Exception Handling Utilities
Handles common TGTG API exceptions including CAPTCHA blocks.
"""

import logging
import requests
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

class TGTGCaptchaException(Exception):
    """Exception raised when TGTG API is blocked by CAPTCHA."""
    pass

class TGTGServiceException(Exception):
    """Exception raised when TGTG service is temporarily unavailable."""
    pass

def is_captcha_blocked(exception: Exception) -> bool:
    """Check if the exception indicates a CAPTCHA block."""
    try:
        # Check if it's a requests exception with 403 status
        if hasattr(exception, 'response') and exception.response is not None:
            if exception.response.status_code == 403:
                # Check response content for captcha URL
                try:
                    response_text = exception.response.text.lower()
                    if 'geo.captcha-delivery.com' in response_text or 'captcha' in response_text:
                        return True
                except:
                    pass
        
        # Check exception message for captcha indicators
        error_msg = str(exception).lower()
        if any(keyword in error_msg for keyword in ['captcha', 'geo.captcha-delivery.com', '403']):
            return True
            
        return False
    except:
        return False

def handle_tgtg_exception(e: Exception, operation: str = "TGTG operation") -> None:
    """Handle TGTG exceptions and raise appropriate custom exceptions."""
    if is_captcha_blocked(e):
        logger.warning(f"TGTG API blocked by CAPTCHA during {operation}: {str(e)}")
        raise TGTGCaptchaException(f"TGTG service temporarily blocked by anti-bot protection. Please try again later.")
    
    # Check for other common HTTP errors
    if hasattr(e, 'response') and e.response is not None:
        status_code = e.response.status_code
        if status_code == 429:
            raise TGTGServiceException("TGTG API rate limit exceeded. Please try again later.")
        elif status_code >= 500:
            raise TGTGServiceException("TGTG service is temporarily unavailable. Please try again later.")
        elif status_code == 401:
            raise TGTGServiceException("TGTG authentication expired. Please re-authenticate.")
    
    # Re-raise original exception if not handled
    raise e

def safe_tgtg_call(func: Callable, operation: str = "TGTG operation", *args, **kwargs) -> Any:
    """Safely call a TGTG API function with exception handling."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        handle_tgtg_exception(e, operation)

def get_user_friendly_error_message(e: Exception) -> str:
    """Get a user-friendly error message for TGTG exceptions."""
    if isinstance(e, TGTGCaptchaException):
        return (
            "🚫 <b>Service Temporarily Unavailable</b>\n\n"
            "TGTG has temporarily blocked API access due to high usage.\n\n"
            "🔄 <b>What to do:</b>\n"
            "• Try again in 15-30 minutes\n"
            "• The service should automatically recover\n"
            "• This is a temporary protective measure by TGTG"
        )
    elif isinstance(e, TGTGServiceException):
        return (
            f"⚠️ <b>Service Issue</b>\n\n"
            f"{str(e)}\n\n"
            f"💡 <i>Please try again in a few minutes.</i>"
        )
    else:
        return (
            f"❌ <b>Unexpected Error</b>\n\n"
            f"Something went wrong: {str(e)}\n\n"
            f"💡 <i>Please try again or contact support if this persists.</i>"
        )
