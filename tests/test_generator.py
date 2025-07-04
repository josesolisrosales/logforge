"""Tests for log generator module."""

import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from logsmith.core.config import LogConfig
from logsmith.core.generator import LogGenerator
from logsmith.core.formats import LogFormat


class TestLogGenerator:
    """Test LogGenerator class."""
    
    def test_init(self):
        """Test generator initialization."""
        config = LogConfig(total_logs=100)
        generator = LogGenerator(config)
        
        assert generator.config == config
        assert generator.formatter is not None
        assert generator.data_generator is not None
        assert generator.performance_monitor is not None
    
    def test_precompute_data(self):
        """Test data precomputation."""
        config = LogConfig(total_logs=100)
        generator = LogGenerator(config)
        
        assert len(generator.log_levels) > 0
        assert len(generator.log_level_weights) > 0
        assert len(generator.log_levels) == len(generator.log_level_weights)
    
    def test_generate_single_log(self):
        """Test single log generation."""
        config = LogConfig()
        generator = LogGenerator(config)
        
        log_entry = generator.generate_single_log()
        
        assert "timestamp" in log_entry
        assert "level" in log_entry
        assert "message" in log_entry
        assert isinstance(log_entry["timestamp"], datetime)
        assert log_entry["level"] in config.log_levels
        assert isinstance(log_entry["message"], str)
    
    def test_generate_single_log_with_params(self):
        """Test single log generation with parameters."""
        config = LogConfig()
        generator = LogGenerator(config)
        
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        level = "ERROR"
        
        log_entry = generator.generate_single_log(timestamp=timestamp, level=level)
        
        assert log_entry["timestamp"] == timestamp
        assert log_entry["level"] == level
    
    def test_generate_batch(self):
        """Test batch generation."""
        config = LogConfig()
        generator = LogGenerator(config)
        
        batch_size = 10
        batch = list(generator.generate_batch(batch_size))
        
        assert len(batch) == batch_size
        for log_entry in batch:
            assert "timestamp" in log_entry
            assert "level" in log_entry
            assert "message" in log_entry
    
    def test_generate_batch_with_precomputed_timestamps(self):
        """Test batch generation with precomputed timestamps."""
        config = LogConfig(total_logs=100)
        config.performance.precompute_timestamps = True
        generator = LogGenerator(config)
        
        batch_size = 10
        batch = list(generator.generate_batch(batch_size))
        
        assert len(batch) == batch_size
        # Check that timestamps are sorted
        timestamps = [entry["timestamp"] for entry in batch]
        assert timestamps == sorted(timestamps)
    
    def test_format_batch(self):
        """Test batch formatting."""
        config = LogConfig()
        generator = LogGenerator(config)
        
        batch = [
            {"timestamp": datetime.now(), "level": "INFO", "message": "Test 1"},
            {"timestamp": datetime.now(), "level": "ERROR", "message": "Test 2"}
        ]
        
        formatted = generator._format_batch(batch)
        
        assert len(formatted) == 2
        assert all(isinstance(line, str) for line in formatted)
        assert "Test 1" in formatted[0]
        assert "Test 2" in formatted[1]
    
    def test_generate_sequential_to_file(self):
        """Test sequential generation to file."""
        config = LogConfig(total_logs=100)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            config.output.file_path = Path(f.name)
            temp_path = f.name
        
        try:
            generator = LogGenerator(config)
            generator.generate_sequential()
            
            # Check that file was created and has content
            with open(temp_path, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == 100
            assert all(line.strip() for line in lines)  # No empty lines
            
        finally:
            Path(temp_path).unlink()
    
    def test_generate_sequential_to_stdout(self):
        """Test sequential generation to stdout."""
        config = LogConfig(total_logs=10)
        generator = LogGenerator(config)
        
        with patch('sys.stdout') as mock_stdout:
            generator.generate_sequential()
            assert mock_stdout.write.called
    
    def test_generate_with_progress_callback(self):
        """Test generation with progress callback."""
        config = LogConfig(total_logs=50)
        generator = LogGenerator(config)
        
        progress_calls = []
        
        def progress_callback(percentage, logs_generated):
            progress_calls.append((percentage, logs_generated))
        
        generator.generate_sequential(progress_callback)
        
        assert len(progress_calls) > 0
        # Check that progress increases
        assert progress_calls[-1][0] == 1.0  # Should end at 100%
        assert progress_calls[-1][1] == 50   # Should have generated 50 logs
    
    def test_generate_with_compression(self):
        """Test generation with compression."""
        config = LogConfig(total_logs=10)
        config.output.compression = "gzip"
        
        with tempfile.NamedTemporaryFile(suffix='.log.gz', delete=False) as f:
            config.output.file_path = Path(f.name)
            temp_path = f.name
        
        try:
            generator = LogGenerator(config)
            generator.generate_sequential()
            
            # Check that compressed file was created
            assert Path(temp_path).exists()
            
            # Check that we can read the compressed file
            import gzip
            with gzip.open(temp_path, 'rt') as f:
                lines = f.readlines()
            
            assert len(lines) == 10
            
        finally:
            Path(temp_path).unlink()
    
    def test_generate_json_format(self):
        """Test generation with JSON format."""
        config = LogConfig(total_logs=5)
        config.output.format = "json"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config.output.file_path = Path(f.name)
            temp_path = f.name
        
        try:
            generator = LogGenerator(config)
            generator.generate_sequential()
            
            # Check that each line is valid JSON
            with open(temp_path, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == 5
            for line in lines:
                parsed = json.loads(line.strip())
                assert "timestamp" in parsed
                assert "level" in parsed
                assert "message" in parsed
            
        finally:
            Path(temp_path).unlink()
    
    def test_generate_apache_format(self):
        """Test generation with Apache format."""
        config = LogConfig(total_logs=5)
        config.output.format = "apache_common"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            config.output.file_path = Path(f.name)
            temp_path = f.name
        
        try:
            generator = LogGenerator(config)
            generator.generate_sequential()
            
            # Check that log format looks like Apache
            with open(temp_path, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == 5
            for line in lines:
                # Apache format should have IP, timestamp, request, status, size
                assert '"GET ' in line or '"POST ' in line
                assert ' 200 ' in line or ' 404 ' in line  # Status codes
            
        finally:
            Path(temp_path).unlink()
    
    def test_estimate_generation_time(self):
        """Test generation time estimation."""
        config = LogConfig(total_logs=1000)
        generator = LogGenerator(config)
        
        estimated_time = generator.estimate_generation_time()
        
        assert isinstance(estimated_time, float)
        assert estimated_time > 0
    
    def test_estimate_generation_time_with_workers(self):
        """Test generation time estimation with workers."""
        config = LogConfig(total_logs=1000)
        config.performance.workers = 4
        generator = LogGenerator(config)
        
        estimated_time = generator.estimate_generation_time()
        
        assert isinstance(estimated_time, float)
        assert estimated_time > 0
    
    def test_validate_config(self):
        """Test configuration validation."""
        config = LogConfig(total_logs=100)
        generator = LogGenerator(config)
        
        warnings = generator.validate_config()
        
        assert isinstance(warnings, list)
        # Small dataset should have no warnings
        assert len(warnings) == 0
    
    def test_validate_config_with_warnings(self):
        """Test configuration validation with warnings."""
        config = LogConfig(total_logs=10_000_000)  # Large dataset
        config.performance.batch_size = 100  # Small batch size
        generator = LogGenerator(config)
        
        warnings = generator.validate_config()
        
        assert isinstance(warnings, list)
        assert len(warnings) > 0
        assert any("batch size" in warning.lower() for warning in warnings)
    
    def test_get_performance_stats(self):
        """Test performance statistics."""
        config = LogConfig(total_logs=10)
        generator = LogGenerator(config)
        
        # Generate some logs
        generator.generate_sequential()
        
        stats = generator.get_performance_stats()
        
        assert isinstance(stats, dict)
        assert "duration_seconds" in stats
        assert "logs_per_second" in stats
        assert "total_logs_generated" in stats
    
    def test_web_log_fields(self):
        """Test generation of web log fields."""
        config = LogConfig(total_logs=5)
        config.output.format = "apache_common"
        generator = LogGenerator(config)
        
        log_entry = generator.generate_single_log()
        
        # Should have web-specific fields
        assert "host" in log_entry
        assert "request" in log_entry
        assert "status" in log_entry
        assert "size" in log_entry
    
    def test_syslog_fields(self):
        """Test generation of syslog fields."""
        config = LogConfig(total_logs=5)
        config.output.format = "syslog"
        generator = LogGenerator(config)
        
        log_entry = generator.generate_single_log()
        
        # Should have syslog-specific fields
        assert "hostname" in log_entry
        assert "process" in log_entry
        assert "pid" in log_entry
    
    def test_custom_fields(self):
        """Test custom fields in log entries."""
        custom_fields = {"app_name": "test_app", "version": "1.0"}
        config = LogConfig(total_logs=5, custom_fields=custom_fields)
        generator = LogGenerator(config)
        
        log_entry = generator.generate_single_log()
        
        assert log_entry["app_name"] == "test_app"
        assert log_entry["version"] == "1.0"
    
    def test_generate_with_small_batch_size(self):
        """Test generation with small batch size."""
        config = LogConfig(total_logs=25)
        config.performance.batch_size = 10
        generator = LogGenerator(config)
        
        generator.generate_sequential()
        
        stats = generator.get_performance_stats()
        assert stats["total_logs_generated"] == 25
    
    def test_generate_with_headers(self):
        """Test generation with headers (CSV format)."""
        config = LogConfig(total_logs=5)
        config.output.format = "csv"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            config.output.file_path = Path(f.name)
            temp_path = f.name
        
        try:
            generator = LogGenerator(config)
            generator.generate_sequential()
            
            # Check that CSV file has headers
            with open(temp_path, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == 6  # 5 data lines + 1 header
            assert "timestamp" in lines[0]  # Header line
            
        finally:
            Path(temp_path).unlink()
    
    @patch('multiprocessing.cpu_count', return_value=4)
    def test_generate_parallel_decision(self, mock_cpu_count):
        """Test automatic decision for parallel generation."""
        config = LogConfig(total_logs=200_000)  # Large enough for parallel
        generator = LogGenerator(config)
        
        # Should use parallel generation for large datasets
        # This is tested indirectly through the generate method
        with patch.object(generator, 'generate_parallel') as mock_parallel:
            generator.generate()
            mock_parallel.assert_called_once()
    
    def test_generate_sequential_decision(self):
        """Test automatic decision for sequential generation."""
        config = LogConfig(total_logs=1000)  # Small dataset
        generator = LogGenerator(config)
        
        # Should use sequential generation for small datasets
        with patch.object(generator, 'generate_sequential') as mock_sequential:
            generator.generate()
            mock_sequential.assert_called_once()
    
    def test_different_log_levels(self):
        """Test generation with different log levels."""
        config = LogConfig(total_logs=100)
        generator = LogGenerator(config)
        
        # Generate a batch and check level distribution
        batch = list(generator.generate_batch(100))
        levels = [entry["level"] for entry in batch]
        
        # Should have variety of levels
        unique_levels = set(levels)
        assert len(unique_levels) > 1
        
        # All levels should be valid
        for level in levels:
            assert level in config.log_levels
    
    def test_message_generation(self):
        """Test message generation variety."""
        config = LogConfig(total_logs=50)
        generator = LogGenerator(config)
        
        # Generate a batch and check message variety
        batch = list(generator.generate_batch(50))
        messages = [entry["message"] for entry in batch]
        
        # Should have variety of messages
        unique_messages = set(messages)
        assert len(unique_messages) > 1
        
        # All messages should be strings
        for message in messages:
            assert isinstance(message, str)
            assert len(message) > 0