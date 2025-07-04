"""Tests for configuration module."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from logsmith.core.config import LogConfig, LogLevelDistribution, TimeConfig, OutputConfig, PerformanceConfig


class TestLogLevelDistribution:
    """Test LogLevelDistribution class."""
    
    def test_default_distribution(self):
        """Test default distribution."""
        dist = LogLevelDistribution()
        assert isinstance(dist.levels, dict)
        assert sum(dist.levels.values()) == pytest.approx(1.0, rel=1e-6)
    
    def test_custom_distribution(self):
        """Test custom distribution."""
        custom_levels = {"INFO": 0.8, "ERROR": 0.2}
        dist = LogLevelDistribution(levels=custom_levels)
        assert dist.levels == custom_levels
    
    def test_invalid_distribution(self):
        """Test invalid distribution validation."""
        with pytest.raises(ValidationError):
            LogLevelDistribution(levels={"INFO": 0.5, "ERROR": 0.3})  # Sum != 1.0


class TestTimeConfig:
    """Test TimeConfig class."""
    
    def test_default_config(self):
        """Test default time configuration."""
        config = TimeConfig()
        assert config.duration == timedelta(days=1)
        assert config.interval == 1.0
        assert config.jitter == 0.1
    
    def test_custom_interval(self):
        """Test custom interval."""
        config = TimeConfig(interval=5.0)
        assert config.interval == 5.0
    
    def test_distribution_interval(self):
        """Test distribution-based interval."""
        config = TimeConfig(interval="uniform")
        assert config.interval == "uniform"
    
    def test_invalid_interval(self):
        """Test invalid interval."""
        with pytest.raises(ValidationError):
            TimeConfig(interval="invalid_distribution")
    
    def test_negative_interval(self):
        """Test negative interval."""
        with pytest.raises(ValidationError):
            TimeConfig(interval=-1.0)


class TestOutputConfig:
    """Test OutputConfig class."""
    
    def test_default_config(self):
        """Test default output configuration."""
        config = OutputConfig()
        assert config.file_path is None
        assert config.format == "standard"
        assert config.compression is None
    
    def test_custom_config(self):
        """Test custom output configuration."""
        config = OutputConfig(
            file_path=Path("/tmp/test.log"),
            format="json",
            compression="gzip"
        )
        assert config.file_path == Path("/tmp/test.log")
        assert config.format == "json"
        assert config.compression == "gzip"


class TestPerformanceConfig:
    """Test PerformanceConfig class."""
    
    def test_default_config(self):
        """Test default performance configuration."""
        config = PerformanceConfig()
        assert config.batch_size == 10000
        assert config.workers is None
        assert config.use_numpy is True
    
    def test_custom_config(self):
        """Test custom performance configuration."""
        config = PerformanceConfig(
            batch_size=5000,
            workers=4,
            use_numpy=False
        )
        assert config.batch_size == 5000
        assert config.workers == 4
        assert config.use_numpy is False
    
    def test_invalid_batch_size(self):
        """Test invalid batch size."""
        with pytest.raises(ValidationError):
            PerformanceConfig(batch_size=0)


class TestLogConfig:
    """Test LogConfig class."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = LogConfig()
        assert config.total_logs == 1000
        assert len(config.log_levels) == 5
        assert isinstance(config.time, TimeConfig)
        assert isinstance(config.output, OutputConfig)
        assert isinstance(config.performance, PerformanceConfig)
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = LogConfig(
            total_logs=5000,
            log_levels=["INFO", "ERROR"],
            time=TimeConfig(interval=2.0),
            output=OutputConfig(format="json"),
            performance=PerformanceConfig(batch_size=1000)
        )
        assert config.total_logs == 5000
        assert config.log_levels == ["INFO", "ERROR"]
        assert config.time.interval == 2.0
        assert config.output.format == "json"
        assert config.performance.batch_size == 1000
    
    def test_logs_per_second(self):
        """Test logs per second calculation."""
        config = LogConfig(time=TimeConfig(interval=2.0))
        assert config.get_logs_per_second() == 0.5
    
    def test_total_duration(self):
        """Test total duration calculation."""
        config = LogConfig(time=TimeConfig(duration=timedelta(hours=2)))
        assert config.get_total_duration() == timedelta(hours=2)
    
    def test_effective_times(self):
        """Test effective time calculations."""
        now = datetime.now()
        config = LogConfig(time=TimeConfig(
            start_time=now,
            end_time=now + timedelta(hours=1)
        ))
        
        assert config.get_effective_start_time() == now
        assert config.get_effective_end_time() == now + timedelta(hours=1)
    
    def test_from_file(self):
        """Test loading configuration from file."""
        config_data = {
            "total_logs": 2000,
            "output": {"format": "json"},
            "performance": {"batch_size": 5000}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = LogConfig.from_file(temp_path)
            assert config.total_logs == 2000
            assert config.output.format == "json"
            assert config.performance.batch_size == 5000
        finally:
            Path(temp_path).unlink()
    
    def test_from_file_not_found(self):
        """Test loading from non-existent file."""
        with pytest.raises(FileNotFoundError):
            LogConfig.from_file("/non/existent/file.json")
    
    def test_to_file(self):
        """Test saving configuration to file."""
        config = LogConfig(total_logs=3000)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            config.to_file(temp_path)
            
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data['total_logs'] == 3000
        finally:
            Path(temp_path).unlink()
    
    def test_invalid_total_logs(self):
        """Test invalid total logs."""
        with pytest.raises(ValidationError):
            LogConfig(total_logs=0)
    
    def test_message_templates(self):
        """Test message templates."""
        config = LogConfig()
        assert isinstance(config.message_templates, dict)
        assert "INFO" in config.message_templates
        assert "ERROR" in config.message_templates
    
    def test_custom_fields(self):
        """Test custom fields."""
        custom_fields = {"app_name": "test", "version": "1.0"}
        config = LogConfig(custom_fields=custom_fields)
        assert config.custom_fields == custom_fields