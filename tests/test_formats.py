"""Tests for log format module."""

import json
from datetime import datetime

import pytest

from logsmith.core.formats import (
    LogFormat, FormatterFactory, StandardFormatter, JSONFormatter,
    ApacheCommonFormatter, ApacheCombinedFormatter, NginxFormatter,
    SyslogFormatter, CSVFormatter, LogfmtFormatter, GELFFormatter,
    CEFFormatter, CustomFormatter
)


class TestStandardFormatter:
    """Test StandardFormatter class."""
    
    def test_basic_format(self):
        """Test basic formatting."""
        formatter = StandardFormatter()
        log_entry = {
            "timestamp": datetime(2023, 1, 1, 12, 0, 0),
            "level": "INFO",
            "message": "Test message"
        }
        
        result = formatter.format(log_entry)
        assert "2023-01-01 12:00:00" in result
        assert "INFO" in result
        assert "Test message" in result
    
    def test_custom_timestamp_format(self):
        """Test custom timestamp format."""
        formatter = StandardFormatter(timestamp_format="%Y-%m-%d")
        log_entry = {
            "timestamp": datetime(2023, 1, 1, 12, 0, 0),
            "level": "INFO",
            "message": "Test message"
        }
        
        result = formatter.format(log_entry)
        assert "2023-01-01" in result
        assert "12:00:00" not in result
    
    def test_no_headers(self):
        """Test that standard formatter has no headers."""
        formatter = StandardFormatter()
        assert formatter.get_headers() is None


class TestJSONFormatter:
    """Test JSONFormatter class."""
    
    def test_basic_format(self):
        """Test basic JSON formatting."""
        formatter = JSONFormatter()
        log_entry = {
            "timestamp": datetime(2023, 1, 1, 12, 0, 0),
            "level": "INFO",
            "message": "Test message"
        }
        
        result = formatter.format(log_entry)
        parsed = json.loads(result)
        
        assert parsed["timestamp"] == "2023-01-01T12:00:00"
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
    
    def test_pretty_format(self):
        """Test pretty JSON formatting."""
        formatter = JSONFormatter(pretty=True)
        log_entry = {
            "timestamp": datetime(2023, 1, 1, 12, 0, 0),
            "level": "INFO",
            "message": "Test message"
        }
        
        result = formatter.format(log_entry)
        assert "\n" in result  # Pretty format should have newlines
        assert "  " in result  # Pretty format should have indentation
    
    def test_complex_data(self):
        """Test formatting complex data structures."""
        formatter = JSONFormatter()
        log_entry = {
            "timestamp": datetime(2023, 1, 1, 12, 0, 0),
            "level": "INFO",
            "message": "Test message",
            "data": {"key": "value", "number": 42},
            "list": [1, 2, 3]
        }
        
        result = formatter.format(log_entry)
        parsed = json.loads(result)
        
        assert parsed["data"]["key"] == "value"
        assert parsed["data"]["number"] == 42
        assert parsed["list"] == [1, 2, 3]


class TestApacheCommonFormatter:
    """Test ApacheCommonFormatter class."""
    
    def test_basic_format(self):
        """Test basic Apache Common Log format."""
        formatter = ApacheCommonFormatter()
        log_entry = {
            "timestamp": datetime(2023, 1, 1, 12, 0, 0),
            "host": "192.168.1.1",
            "request": "GET /index.html HTTP/1.1",
            "status": 200,
            "size": 1024
        }
        
        result = formatter.format(log_entry)
        assert "192.168.1.1" in result
        assert "GET /index.html HTTP/1.1" in result
        assert "200" in result
        assert "1024" in result
    
    def test_default_values(self):
        """Test default values for missing fields."""
        formatter = ApacheCommonFormatter()
        log_entry = {"timestamp": datetime(2023, 1, 1, 12, 0, 0)}
        
        result = formatter.format(log_entry)
        assert "127.0.0.1" in result  # default host
        assert "GET / HTTP/1.1" in result  # default request
        assert "200" in result  # default status
        assert "1024" in result  # default size


class TestApacheCombinedFormatter:
    """Test ApacheCombinedFormatter class."""
    
    def test_basic_format(self):
        """Test basic Apache Combined Log format."""
        formatter = ApacheCombinedFormatter()
        log_entry = {
            "timestamp": datetime(2023, 1, 1, 12, 0, 0),
            "host": "192.168.1.1",
            "request": "GET /index.html HTTP/1.1",
            "status": 200,
            "size": 1024,
            "referer": "http://example.com",
            "user_agent": "Mozilla/5.0"
        }
        
        result = formatter.format(log_entry)
        assert "192.168.1.1" in result
        assert "GET /index.html HTTP/1.1" in result
        assert "200" in result
        assert "1024" in result
        assert "http://example.com" in result
        assert "Mozilla/5.0" in result


class TestNginxFormatter:
    """Test NginxFormatter class."""
    
    def test_basic_format(self):
        """Test basic Nginx log format."""
        formatter = NginxFormatter()
        log_entry = {
            "timestamp": datetime(2023, 1, 1, 12, 0, 0),
            "remote_addr": "192.168.1.1",
            "request": "GET /index.html HTTP/1.1",
            "status": 200,
            "body_bytes_sent": 1024
        }
        
        result = formatter.format(log_entry)
        assert "192.168.1.1" in result
        assert "GET /index.html HTTP/1.1" in result
        assert "200" in result
        assert "1024" in result


class TestSyslogFormatter:
    """Test SyslogFormatter class."""
    
    def test_basic_format(self):
        """Test basic syslog format."""
        formatter = SyslogFormatter()
        log_entry = {
            "timestamp": datetime(2023, 1, 1, 12, 0, 0),
            "level": "INFO",
            "message": "Test message"
        }
        
        result = formatter.format(log_entry)
        assert "Jan 01 12:00:00" in result
        assert "localhost" in result
        assert "Test message" in result
    
    def test_custom_facility(self):
        """Test custom facility."""
        formatter = SyslogFormatter(facility=24)
        log_entry = {
            "timestamp": datetime(2023, 1, 1, 12, 0, 0),
            "level": "INFO",
            "message": "Test message"
        }
        
        result = formatter.format(log_entry)
        # Priority = facility * 8 + severity
        # INFO severity = 6, so priority = 24 * 8 + 6 = 198
        assert "<198>" in result


class TestCSVFormatter:
    """Test CSVFormatter class."""
    
    def test_basic_format(self):
        """Test basic CSV format."""
        formatter = CSVFormatter()
        log_entry = {
            "timestamp": datetime(2023, 1, 1, 12, 0, 0),
            "level": "INFO",
            "message": "Test message"
        }
        
        result = formatter.format(log_entry)
        assert "2023-01-01T12:00:00" in result
        assert "INFO" in result
        assert "Test message" in result
        assert "," in result
    
    def test_custom_fields(self):
        """Test custom fields."""
        formatter = CSVFormatter(fields=["level", "message"])
        log_entry = {
            "timestamp": datetime(2023, 1, 1, 12, 0, 0),
            "level": "INFO",
            "message": "Test message"
        }
        
        result = formatter.format(log_entry)
        assert result == "INFO,Test message"
    
    def test_headers(self):
        """Test CSV headers."""
        formatter = CSVFormatter(fields=["timestamp", "level", "message"])
        headers = formatter.get_headers()
        assert headers == "timestamp,level,message"
    
    def test_escaping(self):
        """Test CSV escaping."""
        formatter = CSVFormatter()
        log_entry = {
            "timestamp": datetime(2023, 1, 1, 12, 0, 0),
            "level": "INFO",
            "message": "Test, message with comma"
        }
        
        result = formatter.format(log_entry)
        assert '"Test, message with comma"' in result


class TestLogfmtFormatter:
    """Test LogfmtFormatter class."""
    
    def test_basic_format(self):
        """Test basic logfmt format."""
        formatter = LogfmtFormatter()
        log_entry = {
            "timestamp": datetime(2023, 1, 1, 12, 0, 0),
            "level": "INFO",
            "message": "Test message"
        }
        
        result = formatter.format(log_entry)
        assert "timestamp=2023-01-01T12:00:00" in result
        assert "level=INFO" in result
        assert "message=\"Test message\"" in result
    
    def test_value_quoting(self):
        """Test value quoting for spaces."""
        formatter = LogfmtFormatter()
        log_entry = {
            "key1": "value with spaces",
            "key2": "simple_value"
        }
        
        result = formatter.format(log_entry)
        assert 'key1="value with spaces"' in result
        assert 'key2=simple_value' in result


class TestGELFFormatter:
    """Test GELFFormatter class."""
    
    def test_basic_format(self):
        """Test basic GELF format."""
        formatter = GELFFormatter()
        log_entry = {
            "timestamp": datetime(2023, 1, 1, 12, 0, 0),
            "level": "INFO",
            "message": "Test message"
        }
        
        result = formatter.format(log_entry)
        parsed = json.loads(result)
        
        assert parsed["version"] == "1.1"
        assert parsed["host"] == "localhost"
        assert parsed["level"] == 6  # INFO severity
        assert parsed["short_message"] == "Test message"
        assert isinstance(parsed["timestamp"], (int, float))
    
    def test_custom_fields(self):
        """Test custom fields with underscore prefix."""
        formatter = GELFFormatter()
        log_entry = {
            "timestamp": datetime(2023, 1, 1, 12, 0, 0),
            "level": "INFO",
            "message": "Test message",
            "custom_field": "custom_value"
        }
        
        result = formatter.format(log_entry)
        parsed = json.loads(result)
        
        assert parsed["_custom_field"] == "custom_value"


class TestCEFFormatter:
    """Test CEFFormatter class."""
    
    def test_basic_format(self):
        """Test basic CEF format."""
        formatter = CEFFormatter()
        log_entry = {
            "level": "INFO",
            "message": "Test event"
        }
        
        result = formatter.format(log_entry)
        assert result.startswith("CEF:0|")
        assert "LogSmith" in result
        assert "LogGenerator" in result
        assert "Test event" in result
    
    def test_severity_mapping(self):
        """Test severity mapping."""
        formatter = CEFFormatter()
        
        # Test different levels
        for level, expected_severity in [
            ("DEBUG", 1),
            ("INFO", 3),
            ("WARNING", 6),
            ("ERROR", 8),
            ("CRITICAL", 10)
        ]:
            log_entry = {"level": level, "message": "Test"}
            result = formatter.format(log_entry)
            assert f"|{expected_severity}|" in result


class TestCustomFormatter:
    """Test CustomFormatter class."""
    
    def test_basic_format(self):
        """Test basic custom format."""
        template = "{timestamp} [{level}] {message}"
        formatter = CustomFormatter(template)
        
        log_entry = {
            "timestamp": datetime(2023, 1, 1, 12, 0, 0),
            "level": "INFO",
            "message": "Test message"
        }
        
        result = formatter.format(log_entry)
        assert "2023-01-01T12:00:00" in result
        assert "[INFO]" in result
        assert "Test message" in result
    
    def test_missing_fields(self):
        """Test handling of missing fields."""
        template = "{timestamp} [{level}] {message} {missing_field}"
        formatter = CustomFormatter(template)
        
        log_entry = {
            "timestamp": datetime(2023, 1, 1, 12, 0, 0),
            "level": "INFO",
            "message": "Test message"
        }
        
        # Should not raise an error
        result = formatter.format(log_entry)
        assert "2023-01-01T12:00:00" in result


class TestFormatterFactory:
    """Test FormatterFactory class."""
    
    def test_create_standard_formatter(self):
        """Test creating standard formatter."""
        formatter = FormatterFactory.create_formatter(LogFormat.STANDARD)
        assert isinstance(formatter, StandardFormatter)
    
    def test_create_json_formatter(self):
        """Test creating JSON formatter."""
        formatter = FormatterFactory.create_formatter(LogFormat.JSON)
        assert isinstance(formatter, JSONFormatter)
    
    def test_create_with_string(self):
        """Test creating formatter with string."""
        formatter = FormatterFactory.create_formatter("json")
        assert isinstance(formatter, JSONFormatter)
    
    def test_create_custom_formatter(self):
        """Test creating custom formatter."""
        formatter = FormatterFactory.create_formatter(
            LogFormat.CUSTOM, 
            template="{timestamp} {message}"
        )
        assert isinstance(formatter, CustomFormatter)
    
    def test_create_custom_without_template(self):
        """Test creating custom formatter without template."""
        with pytest.raises(ValueError, match="Custom formatter requires a template"):
            FormatterFactory.create_formatter(LogFormat.CUSTOM)
    
    def test_unsupported_format(self):
        """Test unsupported format."""
        with pytest.raises(ValueError, match="Unsupported format"):
            # This should raise an error if we try to create a formatter for a non-existent format
            FormatterFactory.create_formatter("non_existent_format")
    
    def test_get_available_formats(self):
        """Test getting available formats."""
        formats = FormatterFactory.get_available_formats()
        assert isinstance(formats, list)
        assert "standard" in formats
        assert "json" in formats
        assert "apache_common" in formats
        assert len(formats) > 5  # Should have multiple formats
    
    def test_create_with_kwargs(self):
        """Test creating formatter with keyword arguments."""
        formatter = FormatterFactory.create_formatter(
            LogFormat.JSON, 
            pretty=True
        )
        assert isinstance(formatter, JSONFormatter)
        assert formatter.pretty is True