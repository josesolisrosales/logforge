#!/usr/bin/env python3
"""
Advanced features examples for LogSmith.

This script demonstrates advanced functionality including
configuration management, performance optimization, and
custom formatting.
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from logforge import LogGenerator, LogConfig
from logforge.core.formats import FormatterFactory, CustomFormatter
from logforge.utils.performance import BenchmarkRunner


def configuration_file_example():
    """Demonstrate loading and saving configuration files."""
    print("=== Configuration File Example ===")
    
    # Create a complex configuration
    config = LogConfig(
        total_logs=50000,
        log_levels=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        level_distribution={
            "levels": {
                "DEBUG": 0.2,
                "INFO": 0.6,
                "WARNING": 0.15,
                "ERROR": 0.04,
                "CRITICAL": 0.01
            }
        },
        time={
            "duration": timedelta(hours=2),
            "interval": "exponential",  # Bursty traffic pattern
            "jitter": 0.3
        },
        output={
            "format": "json",
            "file_path": Path("examples/output/advanced_config.json"),
            "compression": "gzip",
            "buffer_size": 32768
        },
        performance={
            "batch_size": 5000,
            "workers": 2,
            "use_numpy": True,
            "precompute_timestamps": True
        },
        custom_fields={
            "service": "user-service",
            "version": "2.1.0",
            "datacenter": "us-east-1",
            "pod_id": "user-service-abc123"
        },
        message_templates={
            "INFO": [
                "User {user_id} performed action {action}",
                "Request processed successfully for endpoint {endpoint}",
                "Cache hit for key {cache_key} in {cache_time}ms",
                "Database query completed in {query_time}ms",
                "Service health check passed"
            ],
            "WARNING": [
                "Slow response time detected: {response_time}ms for {endpoint}",
                "Memory usage high: {memory_percent}% of available",
                "Connection pool nearly exhausted: {active_connections}/{max_connections}",
                "Rate limit approached for user {user_id}",
                "Deprecated API endpoint {endpoint} used"
            ],
            "ERROR": [
                "Database connection failed: {error_message}",
                "Authentication failed for user {user_id}: {failure_reason}",
                "External service {service_name} returned error {error_code}",
                "File processing failed for {filename}: {error_details}",
                "Payment processing error for transaction {transaction_id}"
            ],
            "CRITICAL": [
                "Service completely unavailable",
                "Database connection pool exhausted",
                "Out of memory condition detected",
                "Security breach attempt detected from {ip_address}",
                "Data corruption detected in {table_name}"
            ]
        }
    )
    
    # Save configuration to file
    config_path = Path("examples/output/advanced_config.json")
    config.to_file(config_path)
    print(f"Configuration saved to: {config_path}")
    
    # Load configuration from file
    loaded_config = LogConfig.from_file(config_path)
    print(f"Configuration loaded successfully")
    print(f"Total logs to generate: {loaded_config.total_logs:,}")
    print(f"Output format: {loaded_config.output.format}")
    print(f"Custom fields: {loaded_config.custom_fields}")
    
    # Generate logs using loaded configuration
    generator = LogGenerator(loaded_config)
    generator.generate()
    
    stats = generator.get_performance_stats()
    print(f"Generated {stats['total_logs_generated']:,} logs")
    print()


def custom_formatter_example():
    """Demonstrate custom log formatting."""
    print("=== Custom Formatter Example ===")
    
    # Create a custom log format template
    custom_template = "[{timestamp}] {level:8} | {component:12} | {message} | duration={duration}ms"
    
    config = LogConfig(
        total_logs=1000,
        output={
            "format": "custom",
            "file_path": Path("examples/output/custom_format.log")
        },
        custom_fields={
            "component": "api-gateway",
            "duration": "42"
        }
    )
    
    # Create generator with custom formatter
    generator = LogGenerator(config)
    generator.formatter = CustomFormatter(custom_template)
    
    generator.generate()
    
    print(f"Generated logs with custom format")
    print(f"Template: {custom_template}")
    print(f"Output file: {config.output.file_path}")
    print()


def performance_benchmark_example():
    """Demonstrate performance benchmarking."""
    print("=== Performance Benchmark Example ===")
    
    # Create benchmark configuration
    benchmark_config = LogConfig(
        total_logs=100000,  # 100K logs
        output={
            "format": "json",
            "file_path": None  # Output to /dev/null (stdout)
        },
        performance={
            "batch_size": 10000,
            "workers": 4
        }
    )
    
    print("Running performance benchmark...")
    print(f"Generating {benchmark_config.total_logs:,} logs...")
    
    # Run benchmark
    results = BenchmarkRunner.run_generation_benchmark(benchmark_config, iterations=3)
    
    # Display results
    print(BenchmarkRunner.format_benchmark_results(results))
    print()


def multiple_formats_example():
    """Generate logs in multiple formats simultaneously."""
    print("=== Multiple Formats Example ===")
    
    base_config = {
        "total_logs": 5000,
        "custom_fields": {
            "app": "multi-format-demo",
            "version": "1.0"
        }
    }
    
    formats = [
        ("json", "multi_format.json"),
        ("apache_common", "multi_format_apache.log"),
        ("csv", "multi_format.csv"),
        ("syslog", "multi_format_syslog.log")
    ]
    
    for fmt, filename in formats:
        print(f"Generating {fmt} format...")
        
        config = LogConfig(
            **base_config,
            output={
                "format": fmt,
                "file_path": Path(f"examples/output/{filename}")
            }
        )
        
        generator = LogGenerator(config)
        generator.generate()
        
        stats = generator.get_performance_stats()
        print(f"  {stats['total_logs_generated']:,} logs in {stats['duration_seconds']:.2f}s")
    
    print("All formats generated successfully!")
    print()


def time_series_example():
    """Generate logs with realistic time series patterns."""
    print("=== Time Series Example ===")
    
    # Simulate a week of logs with varying patterns
    config = LogConfig(
        total_logs=50000,
        time={
            "start_time": datetime.now() - timedelta(days=7),
            "end_time": datetime.now(),
            "interval": "normal",  # Normal distribution around center
            "jitter": 0.2
        },
        output={
            "format": "json",
            "file_path": Path("examples/output/time_series.json")
        },
        level_distribution={
            "levels": {
                "DEBUG": 0.3,
                "INFO": 0.5,
                "WARNING": 0.15,
                "ERROR": 0.04,
                "CRITICAL": 0.01
            }
        },
        custom_fields={
            "source": "time-series-demo"
        }
    )
    
    generator = LogGenerator(config)
    generator.generate()
    
    stats = generator.get_performance_stats()
    print(f"Generated {stats['total_logs_generated']:,} logs over 7-day period")
    print(f"Time range: {config.time.start_time} to {config.time.end_time}")
    print(f"Output file: {config.output.file_path}")
    print()


def memory_efficient_example():
    """Demonstrate memory-efficient generation for large datasets."""
    print("=== Memory Efficient Example ===")
    
    # Generate 1 million logs with memory constraints
    config = LogConfig(
        total_logs=1000000,
        output={
            "format": "json",
            "file_path": Path("examples/output/large_dataset.json.gz"),
            "compression": "gzip",
            "buffer_size": 65536  # Large buffer for efficiency
        },
        performance={
            "batch_size": 20000,  # Large batches
            "workers": 2,  # Limited workers to control memory
            "use_numpy": True,
            "precompute_timestamps": False  # Save memory
        }
    )
    
    generator = LogGenerator(config)
    
    # Show memory warnings
    warnings = generator.validate_config()
    if warnings:
        print("Configuration warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    print(f"Generating {config.total_logs:,} logs...")
    
    # Generate with progress updates
    def progress_callback(percentage, logs_generated):
        if logs_generated % 100000 == 0:
            print(f"  Progress: {logs_generated:,} logs ({percentage:.1%})")
    
    generator.generate(progress_callback)
    
    stats = generator.get_performance_stats()
    print(f"Generated {stats['total_logs_generated']:,} logs")
    print(f"Duration: {stats['duration_seconds']:.2f} seconds")
    print(f"Rate: {stats['logs_per_second']:,.0f} logs/second")
    print(f"Peak memory: {stats['peak_memory_usage_mb']:.1f} MB")
    print(f"Compressed output: {config.output.file_path}")
    print()


def validation_example():
    """Demonstrate configuration validation."""
    print("=== Configuration Validation Example ===")
    
    # Create a configuration that might have issues
    config = LogConfig(
        total_logs=10000000,  # Very large dataset
        performance={
            "batch_size": 100,  # Very small batch size (inefficient)
            "workers": 16  # Many workers (might cause memory issues)
        },
        output={
            "format": "json",
            "file_path": Path("examples/output/validation_test.json")
        }
    )
    
    generator = LogGenerator(config)
    warnings = generator.validate_config()
    
    print("Configuration validation results:")
    if warnings:
        print("Warnings found:")
        for warning in warnings:
            print(f"  ⚠️  {warning}")
    else:
        print("✅ No warnings found")
    
    # Show estimated performance
    estimated_time = generator.estimate_generation_time()
    print(f"Estimated generation time: {estimated_time:.2f} seconds")
    print()


def main():
    """Run all advanced examples."""
    # Create output directory
    Path("examples/output").mkdir(parents=True, exist_ok=True)
    
    print("LogSmith Advanced Features Examples")
    print("=" * 50)
    print()
    
    # Run examples
    configuration_file_example()
    custom_formatter_example()
    performance_benchmark_example()
    multiple_formats_example()
    time_series_example()
    memory_efficient_example()
    validation_example()
    
    print("All advanced examples completed!")
    print("Check the 'examples/output/' directory for generated files.")


if __name__ == "__main__":
    main()