#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zentrale Encoding-Module für FAMO TrafficApp
============================================

Dieses Paket stellt alle zentralen Encoding-Funktionen bereit.
"""

from .guards import (
    assert_no_mojibake,
    trace_text,
    preview_geocode_url,
    setup_utf8_logging,
    smoke_test_encoding,
    BAD_MARKERS
)

from .csv_reader import (
    read_csv_unified,
    write_csv_unified
)

from .http_responses import (
    create_utf8_json_response,
    create_utf8_html_response,
    ensure_utf8_headers
)

from .config import (
    CSV_INPUT_ENCODING,
    CSV_OUTPUT_ENCODING,
    HTTP_CHARSET,
    LOG_ENCODING,
    ENCODING_PRIORITY,
    EXPORT_CONFIG
)

__all__ = [
    # Guards
    "assert_no_mojibake",
    "trace_text", 
    "preview_geocode_url",
    "setup_utf8_logging",
    "smoke_test_encoding",
    "BAD_MARKERS",
    
    # CSV Reader
    "read_csv_unified",
    "write_csv_unified",
    
    # HTTP Responses
    "create_utf8_json_response",
    "create_utf8_html_response", 
    "ensure_utf8_headers",
    
    # Config
    "CSV_INPUT_ENCODING",
    "CSV_OUTPUT_ENCODING",
    "HTTP_CHARSET",
    "LOG_ENCODING",
    "ENCODING_PRIORITY",
    "EXPORT_CONFIG"
]
