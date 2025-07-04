"""Log format definitions and formatters."""

import json
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum

import orjson


class LogFormat(Enum):
    """Supported log formats."""
    
    STANDARD = "standard"
    JSON = "json"
    APACHE_COMMON = "apache_common"
    APACHE_COMBINED = "apache_combined"
    NGINX = "nginx"
    SYSLOG = "syslog"
    CSV = "csv"
    LOGFMT = "logfmt"
    GELF = "gelf"
    CEF = "cef"
    CUSTOM = "custom"


class BaseFormatter(ABC):
    """Base class for log formatters."""
    
    @abstractmethod
    def format(self, log_entry: Dict[str, Any]) -> str:
        """Format a log entry."""
        pass
    
    @abstractmethod
    def get_headers(self) -> Optional[str]:
        """Get headers for the format (if applicable)."""
        pass


class StandardFormatter(BaseFormatter):
    """Standard log formatter: timestamp - level - message."""
    
    def __init__(self, timestamp_format: str = "%Y-%m-%d %H:%M:%S"):
        self.timestamp_format = timestamp_format
    
    def format(self, log_entry: Dict[str, Any]) -> str:
        timestamp = log_entry["timestamp"]
        if isinstance(timestamp, datetime):
            timestamp = timestamp.strftime(self.timestamp_format)
        
        level = log_entry.get("level", "INFO")
        message = log_entry.get("message", "")
        
        return f"{timestamp} - {level} - {message}"
    
    def get_headers(self) -> Optional[str]:
        return None


class JSONFormatter(BaseFormatter):
    """JSON log formatter."""
    
    def __init__(self, pretty: bool = False):
        self.pretty = pretty
    
    def format(self, log_entry: Dict[str, Any]) -> str:
        # Convert datetime to ISO format
        formatted_entry = {}
        for key, value in log_entry.items():
            if isinstance(value, datetime):
                formatted_entry[key] = value.isoformat()
            else:
                formatted_entry[key] = value
        
        if self.pretty:
            return json.dumps(formatted_entry, indent=2)
        else:
            # Use orjson for better performance
            return orjson.dumps(formatted_entry).decode('utf-8')
    
    def get_headers(self) -> Optional[str]:
        return None


class ApacheCommonFormatter(BaseFormatter):
    """Apache Common Log Format (CLF)."""
    
    def format(self, log_entry: Dict[str, Any]) -> str:
        # Format: host ident authuser [timestamp] "request" status size
        host = log_entry.get("host", "127.0.0.1")
        ident = log_entry.get("ident", "-")
        authuser = log_entry.get("authuser", "-")
        timestamp = log_entry.get("timestamp", datetime.now())
        
        if isinstance(timestamp, datetime):
            timestamp_str = timestamp.strftime("[%d/%b/%Y:%H:%M:%S %z]")
        else:
            timestamp_str = f"[{timestamp}]"
        
        request = log_entry.get("request", "GET / HTTP/1.1")
        status = log_entry.get("status", 200)
        size = log_entry.get("size", 1024)
        
        return f'{host} {ident} {authuser} {timestamp_str} "{request}" {status} {size}'
    
    def get_headers(self) -> Optional[str]:
        return None


class ApacheCombinedFormatter(BaseFormatter):
    """Apache Combined Log Format."""
    
    def format(self, log_entry: Dict[str, Any]) -> str:
        # Common format + referer + user_agent
        common_formatter = ApacheCommonFormatter()
        common_part = common_formatter.format(log_entry)
        
        referer = log_entry.get("referer", "-")
        user_agent = log_entry.get("user_agent", "-")
        
        return f'{common_part} "{referer}" "{user_agent}"'
    
    def get_headers(self) -> Optional[str]:
        return None


class NginxFormatter(BaseFormatter):
    """Nginx log formatter."""
    
    def format(self, log_entry: Dict[str, Any]) -> str:
        # Similar to Apache but with some differences
        remote_addr = log_entry.get("remote_addr", "127.0.0.1")
        remote_user = log_entry.get("remote_user", "-")
        timestamp = log_entry.get("timestamp", datetime.now())
        
        if isinstance(timestamp, datetime):
            timestamp_str = timestamp.strftime("[%d/%b/%Y:%H:%M:%S %z]")
        else:
            timestamp_str = f"[{timestamp}]"
        
        request = log_entry.get("request", "GET / HTTP/1.1")
        status = log_entry.get("status", 200)
        body_bytes_sent = log_entry.get("body_bytes_sent", 1024)
        http_referer = log_entry.get("http_referer", "-")
        http_user_agent = log_entry.get("http_user_agent", "-")
        
        return (f'{remote_addr} - {remote_user} {timestamp_str} '
                f'"{request}" {status} {body_bytes_sent} '
                f'"{http_referer}" "{http_user_agent}"')
    
    def get_headers(self) -> Optional[str]:
        return None


class SyslogFormatter(BaseFormatter):
    """Syslog RFC3164 formatter."""
    
    def __init__(self, facility: int = 16, hostname: str = "localhost"):
        self.facility = facility
        self.hostname = hostname
    
    def format(self, log_entry: Dict[str, Any]) -> str:
        # Priority = Facility * 8 + Severity
        level = log_entry.get("level", "INFO")
        severity_map = {
            "DEBUG": 7,
            "INFO": 6,
            "WARNING": 4,
            "ERROR": 3,
            "CRITICAL": 2,
        }
        severity = severity_map.get(level, 6)
        priority = self.facility * 8 + severity
        
        timestamp = log_entry.get("timestamp", datetime.now())
        if isinstance(timestamp, datetime):
            timestamp_str = timestamp.strftime("%b %d %H:%M:%S")
        else:
            timestamp_str = str(timestamp)
        
        process = log_entry.get("process", "logsmith")
        pid = log_entry.get("pid", "1234")
        message = log_entry.get("message", "")
        
        return f"<{priority}>{timestamp_str} {self.hostname} {process}[{pid}]: {message}"
    
    def get_headers(self) -> Optional[str]:
        return None


class CSVFormatter(BaseFormatter):
    """CSV log formatter."""
    
    def __init__(self, fields: List[str] = None, delimiter: str = ","):
        self.fields = fields or ["timestamp", "level", "message"]
        self.delimiter = delimiter
    
    def format(self, log_entry: Dict[str, Any]) -> str:
        values = []
        for field in self.fields:
            value = log_entry.get(field, "")
            if isinstance(value, datetime):
                value = value.isoformat()
            # Escape CSV values
            value_str = str(value).replace('"', '""')
            if self.delimiter in value_str or '"' in value_str or '\n' in value_str:
                value_str = f'"{value_str}"'
            values.append(value_str)
        
        return self.delimiter.join(values)
    
    def get_headers(self) -> Optional[str]:
        return self.delimiter.join(self.fields)


class LogfmtFormatter(BaseFormatter):
    """Logfmt formatter (key=value pairs)."""
    
    def format(self, log_entry: Dict[str, Any]) -> str:
        pairs = []
        for key, value in log_entry.items():
            if isinstance(value, datetime):
                value = value.isoformat()
            
            # Escape key and value if needed
            key_str = str(key)
            value_str = str(value)
            
            if " " in value_str or "=" in value_str:
                value_str = f'"{value_str}"'
            
            pairs.append(f"{key_str}={value_str}")
        
        return " ".join(pairs)
    
    def get_headers(self) -> Optional[str]:
        return None


class GELFFormatter(BaseFormatter):
    """GELF (Graylog Extended Log Format) formatter."""
    
    def __init__(self, host: str = "localhost", version: str = "1.1"):
        self.host = host
        self.version = version
    
    def format(self, log_entry: Dict[str, Any]) -> str:
        gelf_entry = {
            "version": self.version,
            "host": self.host,
            "timestamp": log_entry.get("timestamp", datetime.now()),
            "level": self._get_syslog_level(log_entry.get("level", "INFO")),
            "short_message": log_entry.get("message", ""),
        }
        
        # Add custom fields with underscore prefix
        for key, value in log_entry.items():
            if key not in ["timestamp", "level", "message"]:
                gelf_entry[f"_{key}"] = value
        
        # Convert datetime to timestamp
        if isinstance(gelf_entry["timestamp"], datetime):
            gelf_entry["timestamp"] = gelf_entry["timestamp"].timestamp()
        
        return orjson.dumps(gelf_entry).decode('utf-8')
    
    def _get_syslog_level(self, level: str) -> int:
        level_map = {
            "DEBUG": 7,
            "INFO": 6,
            "WARNING": 4,
            "ERROR": 3,
            "CRITICAL": 2,
        }
        return level_map.get(level, 6)
    
    def get_headers(self) -> Optional[str]:
        return None


class CEFFormatter(BaseFormatter):
    """Common Event Format (CEF) formatter."""
    
    def __init__(self, device_vendor: str = "LogSmith", device_product: str = "LogGenerator", 
                 device_version: str = "1.0", signature_id: str = "0"):
        self.device_vendor = device_vendor
        self.device_product = device_product
        self.device_version = device_version
        self.signature_id = signature_id
    
    def format(self, log_entry: Dict[str, Any]) -> str:
        # CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension
        severity = self._get_cef_severity(log_entry.get("level", "INFO"))
        name = log_entry.get("message", "Log Event")
        
        # Build extension
        extension_parts = []
        for key, value in log_entry.items():
            if key not in ["level", "message"]:
                if isinstance(value, datetime):
                    value = value.isoformat()
                extension_parts.append(f"{key}={value}")
        
        extension = " ".join(extension_parts)
        
        return (f"CEF:0|{self.device_vendor}|{self.device_product}|"
                f"{self.device_version}|{self.signature_id}|{name}|{severity}|{extension}")
    
    def _get_cef_severity(self, level: str) -> int:
        severity_map = {
            "DEBUG": 1,
            "INFO": 3,
            "WARNING": 6,
            "ERROR": 8,
            "CRITICAL": 10,
        }
        return severity_map.get(level, 3)
    
    def get_headers(self) -> Optional[str]:
        return None


class CustomFormatter(BaseFormatter):
    """Custom formatter using template strings."""
    
    def __init__(self, template: str):
        self.template = template
    
    def format(self, log_entry: Dict[str, Any]) -> str:
        # Convert datetime objects to strings
        formatted_entry = {}
        for key, value in log_entry.items():
            if isinstance(value, datetime):
                formatted_entry[key] = value.isoformat()
            else:
                formatted_entry[key] = value
        
        try:
            return self.template.format(**formatted_entry)
        except KeyError as e:
            # Handle missing keys gracefully
            return self.template.format_map(formatted_entry)
    
    def get_headers(self) -> Optional[str]:
        return None


class FormatterFactory:
    """Factory for creating log formatters."""
    
    _formatters = {
        LogFormat.STANDARD: StandardFormatter,
        LogFormat.JSON: JSONFormatter,
        LogFormat.APACHE_COMMON: ApacheCommonFormatter,
        LogFormat.APACHE_COMBINED: ApacheCombinedFormatter,
        LogFormat.NGINX: NginxFormatter,
        LogFormat.SYSLOG: SyslogFormatter,
        LogFormat.CSV: CSVFormatter,
        LogFormat.LOGFMT: LogfmtFormatter,
        LogFormat.GELF: GELFFormatter,
        LogFormat.CEF: CEFFormatter,
    }
    
    @classmethod
    def create_formatter(cls, format_type: Union[LogFormat, str], **kwargs) -> BaseFormatter:
        """Create a formatter instance."""
        if isinstance(format_type, str):
            format_type = LogFormat(format_type)
        
        if format_type == LogFormat.CUSTOM:
            template = kwargs.get("template")
            if not template:
                raise ValueError("Custom formatter requires a template")
            return CustomFormatter(template)
        
        formatter_class = cls._formatters.get(format_type)
        if not formatter_class:
            raise ValueError(f"Unsupported format: {format_type}")
        
        return formatter_class(**kwargs)
    
    @classmethod
    def get_available_formats(cls) -> List[str]:
        """Get list of available format names."""
        return [fmt.value for fmt in LogFormat]