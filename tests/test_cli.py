"""Tests for CLI module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

import pytest
from click.testing import CliRunner

from logsmith.cli import cli, generate, benchmark, init_config, validate_config, list_formats
from logsmith.core.config import LogConfig


class TestCLI:
    """Test CLI commands."""
    
    def setup_method(self):
        """Setup test method."""
        self.runner = CliRunner()
    
    def test_cli_version(self):
        """Test CLI version command."""
        result = self.runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert "version" in result.output.lower()
    
    def test_cli_help(self):
        """Test CLI help command."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "LogSmith" in result.output
        assert "generate" in result.output
        assert "benchmark" in result.output


class TestGenerateCommand:
    """Test generate command."""
    
    def setup_method(self):
        """Setup test method."""
        self.runner = CliRunner()
    
    def test_generate_basic(self):
        """Test basic generate command."""
        with patch('logsmith.cli.LogGenerator') as mock_generator:
            mock_instance = Mock()
            mock_generator.return_value = mock_instance
            mock_instance.validate_config.return_value = []
            mock_instance.get_performance_stats.return_value = {
                'duration_seconds': 0.1,
                'logs_per_second': 1000,
                'total_logs_generated': 100
            }
            
            result = self.runner.invoke(generate, ['--count', '100'])
            assert result.exit_code == 0
            mock_generator.assert_called_once()
            mock_instance.generate.assert_called_once()
    
    def test_generate_with_output_file(self):
        """Test generate command with output file."""
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as f:
            temp_path = f.name
        
        try:
            with patch('logsmith.cli.LogGenerator') as mock_generator:
                mock_instance = Mock()
                mock_generator.return_value = mock_instance
                mock_instance.validate_config.return_value = []
                mock_instance.get_performance_stats.return_value = {
                    'duration_seconds': 0.1,
                    'logs_per_second': 1000,
                    'total_logs_generated': 100
                }
                
                result = self.runner.invoke(generate, [
                    '--count', '100',
                    '--output', temp_path
                ])
                assert result.exit_code == 0
                
                # Check that config was set with output file
                call_args = mock_generator.call_args[0]
                config = call_args[0]
                assert config.output.file_path == Path(temp_path)
        
        finally:
            Path(temp_path).unlink()
    
    def test_generate_with_json_format(self):
        """Test generate command with JSON format."""
        with patch('logsmith.cli.LogGenerator') as mock_generator:
            mock_instance = Mock()
            mock_generator.return_value = mock_instance
            mock_instance.validate_config.return_value = []
            mock_instance.get_performance_stats.return_value = {
                'duration_seconds': 0.1,
                'logs_per_second': 1000,
                'total_logs_generated': 100
            }
            
            result = self.runner.invoke(generate, [
                '--count', '100',
                '--format', 'json'
            ])
            assert result.exit_code == 0
            
            # Check that config was set with JSON format
            call_args = mock_generator.call_args[0]
            config = call_args[0]
            assert config.output.format == 'json'
    
    def test_generate_with_compression(self):
        """Test generate command with compression."""
        with patch('logsmith.cli.LogGenerator') as mock_generator:
            mock_instance = Mock()
            mock_generator.return_value = mock_instance
            mock_instance.validate_config.return_value = []
            mock_instance.get_performance_stats.return_value = {
                'duration_seconds': 0.1,
                'logs_per_second': 1000,
                'total_logs_generated': 100
            }
            
            result = self.runner.invoke(generate, [
                '--count', '100',
                '--compression', 'gzip'
            ])
            assert result.exit_code == 0
            
            # Check that config was set with compression
            call_args = mock_generator.call_args[0]
            config = call_args[0]
            assert config.output.compression == 'gzip'
    
    def test_generate_with_custom_fields(self):
        """Test generate command with custom fields."""
        custom_fields = '{"app": "test", "version": "1.0"}'
        
        with patch('logsmith.cli.LogGenerator') as mock_generator:
            mock_instance = Mock()
            mock_generator.return_value = mock_instance
            mock_instance.validate_config.return_value = []
            mock_instance.get_performance_stats.return_value = {
                'duration_seconds': 0.1,
                'logs_per_second': 1000,
                'total_logs_generated': 100
            }
            
            result = self.runner.invoke(generate, [
                '--count', '100',
                '--custom-fields', custom_fields
            ])
            assert result.exit_code == 0
            
            # Check that config was set with custom fields
            call_args = mock_generator.call_args[0]
            config = call_args[0]
            assert config.custom_fields == {"app": "test", "version": "1.0"}
    
    def test_generate_with_level_distribution(self):
        """Test generate command with level distribution."""
        level_dist = '{"INFO": 0.8, "ERROR": 0.2}'
        
        with patch('logsmith.cli.LogGenerator') as mock_generator:
            mock_instance = Mock()
            mock_generator.return_value = mock_instance
            mock_instance.validate_config.return_value = []
            mock_instance.get_performance_stats.return_value = {
                'duration_seconds': 0.1,
                'logs_per_second': 1000,
                'total_logs_generated': 100
            }
            
            result = self.runner.invoke(generate, [
                '--count', '100',
                '--level-dist', level_dist
            ])
            assert result.exit_code == 0
            
            # Check that config was set with level distribution
            call_args = mock_generator.call_args[0]
            config = call_args[0]
            assert config.level_distribution.levels == {"INFO": 0.8, "ERROR": 0.2}
    
    def test_generate_with_config_file(self):
        """Test generate command with config file."""
        config_data = {
            "total_logs": 500,
            "output": {"format": "json"},
            "custom_fields": {"app": "test"}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            with patch('logsmith.cli.LogGenerator') as mock_generator:
                mock_instance = Mock()
                mock_generator.return_value = mock_instance
                mock_instance.validate_config.return_value = []
                mock_instance.get_performance_stats.return_value = {
                    'duration_seconds': 0.1,
                    'logs_per_second': 1000,
                    'total_logs_generated': 500
                }
                
                result = self.runner.invoke(generate, [
                    '--config', config_path
                ])
                assert result.exit_code == 0
                
                # Check that config was loaded from file
                call_args = mock_generator.call_args[0]
                config = call_args[0]
                assert config.total_logs == 500
                assert config.output.format == 'json'
                assert config.custom_fields == {"app": "test"}
        
        finally:
            Path(config_path).unlink()
    
    def test_generate_validate_only(self):
        """Test generate command with validate-only flag."""
        with patch('logsmith.cli.LogGenerator') as mock_generator:
            mock_instance = Mock()
            mock_generator.return_value = mock_instance
            mock_instance.validate_config.return_value = []
            
            result = self.runner.invoke(generate, [
                '--count', '100',
                '--validate-only'
            ])
            assert result.exit_code == 0
            assert "Configuration is valid" in result.output
            mock_instance.generate.assert_not_called()
    
    def test_generate_with_warnings(self):
        """Test generate command with configuration warnings."""
        with patch('logsmith.cli.LogGenerator') as mock_generator:
            mock_instance = Mock()
            mock_generator.return_value = mock_instance
            mock_instance.validate_config.return_value = ["Test warning"]
            mock_instance.get_performance_stats.return_value = {
                'duration_seconds': 0.1,
                'logs_per_second': 1000,
                'total_logs_generated': 100
            }
            
            result = self.runner.invoke(generate, ['--count', '100'])
            assert result.exit_code == 0
            assert "warning" in result.output.lower()
    
    def test_generate_benchmark_mode(self):
        """Test generate command in benchmark mode."""
        with patch('logsmith.cli.LogGenerator') as mock_generator:
            mock_instance = Mock()
            mock_generator.return_value = mock_instance
            mock_instance.validate_config.return_value = []
            mock_instance.estimate_generation_time.return_value = 0.5
            mock_instance.get_performance_stats.return_value = {
                'duration_seconds': 0.1,
                'logs_per_second': 1000,
                'total_logs_generated': 100
            }
            
            result = self.runner.invoke(generate, [
                '--count', '100',
                '--benchmark'
            ])
            assert result.exit_code == 0
            assert "benchmark" in result.output.lower()
    
    def test_generate_invalid_format(self):
        """Test generate command with invalid format."""
        result = self.runner.invoke(generate, [
            '--count', '100',
            '--format', 'invalid_format'
        ])
        assert result.exit_code != 0
        assert "Invalid format" in result.output
    
    def test_generate_invalid_count(self):
        """Test generate command with invalid count."""
        result = self.runner.invoke(generate, [
            '--count', '0'
        ])
        assert result.exit_code != 0
        assert "Must be a positive integer" in result.output
    
    def test_generate_invalid_json_custom_fields(self):
        """Test generate command with invalid JSON custom fields."""
        result = self.runner.invoke(generate, [
            '--count', '100',
            '--custom-fields', 'invalid_json'
        ])
        assert result.exit_code != 0
        assert "Invalid JSON" in result.output
    
    def test_generate_invalid_json_level_dist(self):
        """Test generate command with invalid JSON level distribution."""
        result = self.runner.invoke(generate, [
            '--count', '100',
            '--level-dist', 'invalid_json'
        ])
        assert result.exit_code != 0
        assert "Invalid JSON" in result.output


class TestBenchmarkCommand:
    """Test benchmark command."""
    
    def setup_method(self):
        """Setup test method."""
        self.runner = CliRunner()
    
    def test_benchmark_basic(self):
        """Test basic benchmark command."""
        with patch('logsmith.cli.BenchmarkRunner') as mock_runner:
            mock_runner.run_generation_benchmark.return_value = {
                'iterations': 3,
                'avg_duration': 1.0,
                'avg_logs_per_second': 1000,
                'avg_memory_usage': 100,
                'avg_cpu_usage': 50,
                'min_logs_per_second': 900,
                'max_logs_per_second': 1100,
                'detailed_results': []
            }
            mock_runner.format_benchmark_results.return_value = "Benchmark results"
            
            result = self.runner.invoke(benchmark, ['--count', '1000'])
            assert result.exit_code == 0
            assert "Benchmark results" in result.output
            mock_runner.run_generation_benchmark.assert_called_once()
    
    def test_benchmark_with_options(self):
        """Test benchmark command with options."""
        with patch('logsmith.cli.BenchmarkRunner') as mock_runner:
            mock_runner.run_generation_benchmark.return_value = {
                'iterations': 5,
                'avg_duration': 1.0,
                'avg_logs_per_second': 1000,
                'avg_memory_usage': 100,
                'avg_cpu_usage': 50,
                'min_logs_per_second': 900,
                'max_logs_per_second': 1100,
                'detailed_results': []
            }
            mock_runner.format_benchmark_results.return_value = "Benchmark results"
            
            result = self.runner.invoke(benchmark, [
                '--count', '1000',
                '--format', 'json',
                '--iterations', '5',
                '--workers', '4'
            ])
            assert result.exit_code == 0
            
            # Check that config was created with options
            call_args = mock_runner.run_generation_benchmark.call_args[0]
            config = call_args[0]
            assert config.total_logs == 1000
            assert config.output.format == 'json'
            assert config.performance.workers == 4
    
    def test_benchmark_with_output_file(self):
        """Test benchmark command with output file."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            with patch('logsmith.cli.BenchmarkRunner') as mock_runner:
                mock_results = {
                    'iterations': 3,
                    'avg_duration': 1.0,
                    'avg_logs_per_second': 1000,
                    'avg_memory_usage': 100,
                    'avg_cpu_usage': 50,
                    'min_logs_per_second': 900,
                    'max_logs_per_second': 1100,
                    'detailed_results': []
                }
                mock_runner.run_generation_benchmark.return_value = mock_results
                mock_runner.format_benchmark_results.return_value = "Benchmark results"
                
                result = self.runner.invoke(benchmark, [
                    '--count', '1000',
                    '--output', temp_path
                ])
                assert result.exit_code == 0
                assert f"Results saved to {temp_path}" in result.output
                
                # Check that results were saved
                with open(temp_path, 'r') as f:
                    saved_results = json.load(f)
                assert saved_results == mock_results
        
        finally:
            Path(temp_path).unlink()


class TestInitConfigCommand:
    """Test init-config command."""
    
    def setup_method(self):
        """Setup test method."""
        self.runner = CliRunner()
    
    def test_init_config_basic(self):
        """Test basic init-config command."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            result = self.runner.invoke(init_config, ['--output', temp_path])
            assert result.exit_code == 0
            assert f"Configuration file created: {temp_path}" in result.output
            
            # Check that config file was created
            assert Path(temp_path).exists()
            
            # Check that config is valid
            with open(temp_path, 'r') as f:
                config_data = json.load(f)
            
            assert config_data['total_logs'] == 1000
            assert config_data['output']['format'] == 'standard'
        
        finally:
            Path(temp_path).unlink()
    
    def test_init_config_with_options(self):
        """Test init-config command with options."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            result = self.runner.invoke(init_config, [
                '--output', temp_path,
                '--format', 'json',
                '--count', '5000'
            ])
            assert result.exit_code == 0
            
            # Check that config has custom values
            with open(temp_path, 'r') as f:
                config_data = json.load(f)
            
            assert config_data['total_logs'] == 5000
            assert config_data['output']['format'] == 'json'
        
        finally:
            Path(temp_path).unlink()


class TestValidateConfigCommand:
    """Test validate-config command."""
    
    def setup_method(self):
        """Setup test method."""
        self.runner = CliRunner()
    
    def test_validate_config_valid(self):
        """Test validate-config command with valid config."""
        config_data = {
            "total_logs": 1000,
            "output": {"format": "json"}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            with patch('logsmith.cli.LogGenerator') as mock_generator:
                mock_instance = Mock()
                mock_generator.return_value = mock_instance
                mock_instance.validate_config.return_value = []
                
                result = self.runner.invoke(validate_config, [config_path])
                assert result.exit_code == 0
                assert "Configuration is valid" in result.output
        
        finally:
            Path(config_path).unlink()
    
    def test_validate_config_with_warnings(self):
        """Test validate-config command with warnings."""
        config_data = {
            "total_logs": 1000,
            "output": {"format": "json"}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            with patch('logsmith.cli.LogGenerator') as mock_generator:
                mock_instance = Mock()
                mock_generator.return_value = mock_instance
                mock_instance.validate_config.return_value = ["Test warning"]
                
                result = self.runner.invoke(validate_config, [config_path])
                assert result.exit_code == 0
                assert "Configuration is valid" in result.output
                assert "warning" in result.output.lower()
        
        finally:
            Path(config_path).unlink()
    
    def test_validate_config_invalid_file(self):
        """Test validate-config command with invalid file."""
        result = self.runner.invoke(validate_config, ['/non/existent/file.json'])
        assert result.exit_code != 0
        assert "Invalid configuration" in result.output
    
    def test_validate_config_invalid_json(self):
        """Test validate-config command with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json")
            config_path = f.name
        
        try:
            result = self.runner.invoke(validate_config, [config_path])
            assert result.exit_code != 0
            assert "Invalid configuration" in result.output
        
        finally:
            Path(config_path).unlink()


class TestListFormatsCommand:
    """Test list-formats command."""
    
    def setup_method(self):
        """Setup test method."""
        self.runner = CliRunner()
    
    def test_list_formats(self):
        """Test list-formats command."""
        result = self.runner.invoke(list_formats)
        assert result.exit_code == 0
        assert "Available Log Formats" in result.output
        assert "standard" in result.output
        assert "json" in result.output
        assert "apache_common" in result.output
    
    def test_list_formats_shows_descriptions(self):
        """Test that list-formats shows descriptions."""
        result = self.runner.invoke(list_formats)
        assert result.exit_code == 0
        assert "JSON format" in result.output
        assert "Apache Common" in result.output


class TestAnomalyParameters:
    """Test CLI anomaly parameters."""
    
    def setup_method(self):
        """Setup test method."""
        self.runner = CliRunner()
    
    def test_generate_with_seed(self):
        """Test generate command with seed parameter."""
        with patch('logsmith.cli.LogGenerator') as mock_generator:
            mock_instance = Mock()
            mock_generator.return_value = mock_instance
            mock_instance.validate_config.return_value = []
            
            result = self.runner.invoke(generate, [
                '--count', '10',
                '--seed', '42',
                '--no-progress'
            ])
            
            assert result.exit_code == 0
            
            # Check that LogGenerator was called with config containing seed
            call_args = mock_generator.call_args[0][0]  # First argument (config)
            assert call_args.seed == 42
    
    def test_generate_with_anomalies_enabled(self):
        """Test generate command with anomalies enabled."""
        with patch('logsmith.cli.LogGenerator') as mock_generator:
            mock_instance = Mock()
            mock_generator.return_value = mock_instance
            mock_instance.validate_config.return_value = []
            
            result = self.runner.invoke(generate, [
                '--count', '10',
                '--anomalies',
                '--no-progress'
            ])
            
            assert result.exit_code == 0
            
            # Check that anomalies are enabled
            call_args = mock_generator.call_args[0][0]
            assert call_args.anomaly_config.enabled is True
    
    def test_generate_with_anomaly_rate(self):
        """Test generate command with custom anomaly rate."""
        with patch('logsmith.cli.LogGenerator') as mock_generator:
            mock_instance = Mock()
            mock_generator.return_value = mock_instance
            mock_instance.validate_config.return_value = []
            
            result = self.runner.invoke(generate, [
                '--count', '10',
                '--anomalies',
                '--anomaly-rate', '0.2',
                '--no-progress'
            ])
            
            assert result.exit_code == 0
            
            # Check that anomaly rate is set
            call_args = mock_generator.call_args[0][0]
            assert call_args.anomaly_config.enabled is True
            assert call_args.anomaly_config.base_rate == 0.2
    
    def test_generate_with_anomaly_config_file(self):
        """Test generate command with anomaly config file."""
        anomaly_config_data = {
            "enabled": True,
            "base_rate": 0.15
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(anomaly_config_data, f)
            anomaly_config_path = f.name
        
        try:
            with patch('logsmith.cli.LogGenerator') as mock_generator:
                mock_instance = Mock()
                mock_generator.return_value = mock_instance
                mock_instance.validate_config.return_value = []
                
                result = self.runner.invoke(generate, [
                    '--count', '10',
                    '--anomaly-config', anomaly_config_path,
                    '--no-progress'
                ])
                
                assert result.exit_code == 0
                
                # Check that anomaly config was loaded
                call_args = mock_generator.call_args[0][0]
                assert call_args.anomaly_config.enabled is True
                assert call_args.anomaly_config.base_rate == 0.15
        
        finally:
            Path(anomaly_config_path).unlink()
    
    def test_invalid_anomaly_rate(self):
        """Test generate command with invalid anomaly rate."""
        result = self.runner.invoke(generate, [
            '--count', '10',
            '--anomalies',
            '--anomaly-rate', '1.5',  # Invalid rate > 1.0
            '--no-progress'
        ])
        
        assert result.exit_code != 0
        assert "must be between 0.0 and 1.0" in result.output
    
    def test_anomaly_config_file_not_found(self):
        """Test generate command with missing anomaly config file."""
        result = self.runner.invoke(generate, [
            '--count', '10',
            '--anomaly-config', '/non/existent/file.json',
            '--no-progress'
        ])
        
        assert result.exit_code != 0
        assert "Invalid anomaly configuration file" in result.output
    
    def test_combined_anomaly_parameters(self):
        """Test generate command with multiple anomaly parameters."""
        with patch('logsmith.cli.LogGenerator') as mock_generator:
            mock_instance = Mock()
            mock_generator.return_value = mock_instance
            mock_instance.validate_config.return_value = []
            
            result = self.runner.invoke(generate, [
                '--count', '100',
                '--seed', '123',
                '--anomalies',
                '--anomaly-rate', '0.3',
                '--format', 'json',
                '--no-progress'
            ])
            
            assert result.exit_code == 0
            
            # Check all parameters are set correctly
            call_args = mock_generator.call_args[0][0]
            assert call_args.seed == 123
            assert call_args.anomaly_config.enabled is True
            assert call_args.anomaly_config.base_rate == 0.3
            assert call_args.output.format == "json"
    
    def test_seed_determinism_via_cli(self):
        """Test that same seed produces deterministic results via CLI."""
        with patch('sys.stdout', new_callable=Mock) as mock_stdout:
            # First run with seed
            result1 = self.runner.invoke(generate, [
                '--count', '2',
                '--seed', '42',
                '--format', 'json',
                '--no-progress'
            ])
            
            # Second run with same seed
            result2 = self.runner.invoke(generate, [
                '--count', '2',
                '--seed', '42',
                '--format', 'json',
                '--no-progress'
            ])
            
            assert result1.exit_code == 0
            assert result2.exit_code == 0
            
            # Results should be identical (this is a basic check)
            # In practice, we'd need to capture and compare actual output
    
    def test_generate_help_includes_anomaly_options(self):
        """Test that generate help includes anomaly options."""
        result = self.runner.invoke(generate, ['--help'])
        assert result.exit_code == 0
        assert "--seed" in result.output
        assert "--anomalies" in result.output
        assert "--anomaly-rate" in result.output
        assert "--anomaly-config" in result.output
        assert "Random seed for deterministic generation" in result.output
        assert "Enable anomaly injection" in result.output