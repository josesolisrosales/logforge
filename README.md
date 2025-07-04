# LogForge 🔨

A high-performance, professional-grade log generator for testing, simulation, and development purposes.

[![PyPI version](https://badge.fury.io/py/logforge.svg)](https://badge.fury.io/py/logforge)
[![Python Support](https://img.shields.io/pypi/pyversions/logforge.svg)](https://pypi.org/project/logforge/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/josesolisrosales/logforge/workflows/Tests/badge.svg)](https://github.com/josesolisrosales/logforge/actions)
[![Code Quality](https://github.com/josesolisrosales/logforge/workflows/Code%20Quality/badge.svg)](https://github.com/josesolisrosales/logforge/actions)

## 🚀 Features

- **High Performance**: Generate 250K+ logs per second
- **Multiple Formats**: Support for JSON, Apache, Nginx, Syslog, CSV, and more
- **Realistic Data**: Generate realistic IPs, user agents, timestamps, and messages
- **Anomaly Detection**: Advanced anomaly injection for ML training with temporal patterns
- **Deterministic Generation**: Seed-based reproducible log generation
- **Configurable**: Highly customizable through config files or CLI options
- **Memory Efficient**: Batch processing and streaming output
- **Parallel Processing**: Multi-core support for maximum performance
- **Rich CLI**: Beautiful progress bars and detailed statistics
- **Extensible**: Easy to add custom formats and data generators

## 📦 Installation

```bash
pip install logforge
```


## 🛠️ Quick Start

### Command Line Usage

Generate 1 million logs in JSON format:

```bash
logforge generate --count 1000000 --format json --output logs.json
```

Generate Apache access logs with compression:

```bash
logforge generate \
  --count 500000 \
  --format apache_common \
  --output access.log \
  --compression gzip
```

Run performance benchmark:

```bash
logforge benchmark --count 1000000 --format json
```

### Python API Usage

```python
from logforge import LogGenerator, LogConfig

# Basic usage
config = LogConfig(total_logs=10000, output={"format": "json"})
generator = LogGenerator(config)
generator.generate()

# Advanced configuration
config = LogConfig(
    total_logs=1000000,
    log_levels=["DEBUG", "INFO", "WARNING", "ERROR"],
    level_distribution={
        "levels": {
            "DEBUG": 0.2,
            "INFO": 0.6,
            "WARNING": 0.15,
            "ERROR": 0.05
        }
    },
    output={
        "format": "json",
        "file_path": "app.log",
        "compression": "gzip"
    },
    performance={
        "batch_size": 10000,
        "workers": 4
    },
    custom_fields={
        "app_name": "my-app",
        "version": "1.0.0"
    }
)

generator = LogGenerator(config)
generator.generate()

# Get performance stats
stats = generator.get_performance_stats()
print(f"Generated {stats['total_logs_generated']} logs in {stats['duration_seconds']:.2f} seconds")
print(f"Rate: {stats['logs_per_second']:,.0f} logs/second")
```

## 📊 Supported Log Formats

| Format | Description | Example Output |
|--------|-------------|----------------|
| `standard` | Simple timestamp-level-message | `2023-12-01 10:30:15 - INFO - User login successful` |
| `json` | Structured JSON logs | `{"timestamp": "2023-12-01T10:30:15", "level": "INFO", "message": "User login"}` |
| `apache_common` | Apache Common Log Format | `192.168.1.1 - - [01/Dec/2023:10:30:15 +0000] "GET /index.html HTTP/1.1" 200 1024` |
| `apache_combined` | Apache Combined Log Format | Apache Common + referer + user agent |
| `nginx` | Nginx access log format | Similar to Apache with Nginx-specific fields |
| `syslog` | RFC3164 Syslog format | `<134>Dec 1 10:30:15 hostname app[1234]: Log message` |
| `csv` | Comma-separated values | `"2023-12-01T10:30:15","INFO","User login"` |
| `logfmt` | Key=value format | `timestamp=2023-12-01T10:30:15 level=INFO message="User login"` |
| `gelf` | Graylog Extended Log Format | JSON format for Graylog |
| `cef` | Common Event Format | `CEF:0|Vendor|Product|Version|SignatureID|Name|Severity|Extension` |

## ⚙️ Configuration

### Configuration File

Create a configuration file (`config.json`):

```json
{
  "total_logs": 1000000,
  "log_levels": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
  "level_distribution": {
    "levels": {
      "DEBUG": 0.25,
      "INFO": 0.60,
      "WARNING": 0.12,
      "ERROR": 0.025,
      "CRITICAL": 0.005
    }
  },
  "time": {
    "duration": "24h",
    "interval": 1.0,
    "jitter": 0.1
  },
  "output": {
    "format": "json",
    "file_path": "app.log",
    "compression": "gzip",
    "buffer_size": 65536
  },
  "performance": {
    "batch_size": 10000,
    "workers": 4,
    "use_numpy": true,
    "precompute_timestamps": true
  },
  "custom_fields": {
    "app_name": "my-application",
    "environment": "production",
    "version": "2.1.0"
  },
  "message_templates": {
    "INFO": [
      "User {user_id} logged in successfully",
      "Processing request for {endpoint}",
      "Database query completed in {query_time}ms"
    ],
    "ERROR": [
      "Failed to connect to database: {error}",
      "Authentication failed for user {user_id}",
      "Service {service_name} is unavailable"
    ]
  }
}
```

Use with CLI:

```bash
logforge generate --config config.json
```

Or initialize a config file:

```bash
logforge init-config --output my-config.json --format json --count 1000000
```

### CLI Options

```bash
logforge generate --help
```

Key options:
- `--count`: Number of logs to generate
- `--format`: Log format (see supported formats above)
- `--output`: Output file path (default: stdout)
- `--compression`: Compression format (gzip, bz2, lzma)
- `--workers`: Number of parallel workers
- `--batch-size`: Batch size for processing
- `--benchmark`: Run in benchmark mode
- `--no-progress`: Disable progress bar

## 🏆 Performance

LogForge is designed for high performance:

- **250K+ logs per second** in optimal conditions
- **100K-150K logs per second** in typical usage
- Memory-efficient streaming generation
- Parallel processing with automatic CPU detection
- Optimized data structures and algorithms
- Batch writing to minimize I/O overhead

### Benchmark Results

Performance varies significantly based on configuration. Here are realistic benchmarks on modern 8-core hardware:

#### Optimal Performance (Large Batch Size)
```
Configuration: 10M logs, batch_size=1,000,000, workers=5
Duration: 34.69 seconds
Logs per second: 288,296
Peak memory: 1,598.4 MB
Peak CPU: 109.0%
```

#### Typical Performance (Balanced Configuration)
```
Configuration: 10M logs, batch_size=100,000, workers=1
Duration: 85.04 seconds  
Logs per second: 117,592
Peak memory: 969.4 MB
Peak CPU: 106.5%
```

#### Performance Factors
- **Batch Size**: Most significant impact on performance (larger = faster, but more memory)
- **Workers**: Parallel processing can improve throughput with larger datasets
- **Format**: JSON ~160 bytes/log, affects memory usage and I/O
- **Output**: Writing to `/dev/null` is fastest for benchmarks

### Realistic Expectations
- **1M logs**: 3-8 seconds
- **10M logs**: 35-85 seconds  
- **100M logs**: 6-15 minutes
- **Memory usage**: ~2KB per log in memory during batch processing

Run your own benchmark:

```bash
logforge benchmark --count 10000000 --format json --iterations 3
```

## 🔍 Anomaly Detection

LogForge includes advanced anomaly injection capabilities for ML training data generation:

### Generate Logs with Anomalies

```bash
# Enable anomaly injection with 20% anomaly rate
logforge generate --count 10000 --anomalies --anomaly-rate 0.2 --seed 42

# Use external anomaly configuration
logforge generate --count 10000 --anomaly-config anomaly_config.json
```

### Anomaly Types

- **Security**: failed_auth, brute_force, suspicious_access, privilege_escalation
- **Performance**: high_latency, memory_spike, cpu_spike, slow_query
- **System**: service_unavailable, database_error, network_error
- **Behavioral**: unusual_volume, geographic_anomaly, user_behavior

### Temporal Patterns

- **BURST**: Intense anomaly periods (simulating attacks)
- **GRADUAL_INCREASE**: Slowly developing performance issues
- **PERIODIC**: Regular anomaly cycles
- **SPIKE**: Short-duration intense anomalies

### Example Anomaly Configuration

```json
{
  "enabled": true,
  "base_rate": 0.1,
  "seed": 42,
  "patterns": [
    {
      "pattern_type": "burst",
      "anomaly_types": ["brute_force", "failed_auth"],
      "base_rate": 0.05,
      "peak_rate": 0.8,
      "duration": "10m",
      "start_time": "5m"
    }
  ]
}
```

## 📚 Examples

### Generate Web Server Logs

```bash
# Apache access logs
logforge generate \
  --count 1000000 \
  --format apache_combined \
  --output access.log \
  --duration 7d

# Nginx logs with realistic traffic patterns
logforge generate \
  --count 5000000 \
  --format nginx \
  --output nginx.log \
  --interval exponential \
  --compression gzip
```

### Application Logs

```bash
# JSON application logs
logforge generate \
  --count 100000 \
  --format json \
  --custom-fields '{"app": "api", "version": "2.1.0"}' \
  --level-dist '{"INFO": 0.7, "WARNING": 0.2, "ERROR": 0.1}' \
  --output app.log
```

### System Logs

```bash
# Syslog format
logforge generate \
  --count 50000 \
  --format syslog \
  --output system.log \
  --interval 0.5
```

### CSV for Analysis

```bash
# CSV format for data analysis
logforge generate \
  --count 10000 \
  --format csv \
  --output logs.csv
```

## 🔧 Development

### Setup Development Environment

```bash
git clone https://github.com/josesolisrosales/logforge.git
cd logforge
pip install -e .[dev]
```

### Run Tests

```bash
pytest
```

### Code Quality

```bash
black src/ tests/
isort src/ tests/
flake8 src/ tests/
mypy src/
```

### Building

```bash
python -m build
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Click](https://click.palletsprojects.com/) for the CLI
- [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- [Faker](https://faker.readthedocs.io/) for realistic data generation
- [Pydantic](https://pydantic-docs.helpmanual.io/) for configuration validation

---

**LogForge** - Forge logs like a master craftsman! 🔨⚡
