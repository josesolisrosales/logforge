#!/bin/bash

# LogSmith CLI Examples
# This script demonstrates various CLI usage patterns

echo "LogSmith CLI Examples"
echo "===================="
echo ""

# Create output directory
mkdir -p examples/output

echo "1. Basic log generation"
echo "----------------------"
logsmith generate --count 1000 --format standard --output examples/output/basic.log
echo ""

echo "2. JSON logs with custom fields"
echo "------------------------------"
logsmith generate \
  --count 5000 \
  --format json \
  --output examples/output/json_logs.json \
  --custom-fields '{"app": "example", "version": "1.0", "env": "dev"}'
echo ""

echo "3. Apache access logs"
echo "--------------------"
logsmith generate \
  --count 10000 \
  --format apache_combined \
  --output examples/output/access.log \
  --duration 1h \
  --interval 0.1
echo ""

echo "4. Compressed syslog"
echo "-------------------"
logsmith generate \
  --count 25000 \
  --format syslog \
  --output examples/output/system.log \
  --compression gzip
echo ""

echo "5. High-performance generation"
echo "-----------------------------"
logsmith generate \
  --count 100000 \
  --format json \
  --output examples/output/high_perf.json \
  --workers 4 \
  --batch-size 10000 \
  --benchmark
echo ""

echo "6. Custom log level distribution"
echo "-------------------------------"
logsmith generate \
  --count 5000 \
  --format json \
  --output examples/output/custom_dist.json \
  --level-dist '{"INFO": 0.8, "WARNING": 0.15, "ERROR": 0.05}'
echo ""

echo "7. CSV format for analysis"
echo "-------------------------"
logsmith generate \
  --count 10000 \
  --format csv \
  --output examples/output/analysis.csv
echo ""

echo "8. Nginx logs with time patterns"
echo "-------------------------------"
logsmith generate \
  --count 20000 \
  --format nginx \
  --output examples/output/nginx.log \
  --interval exponential \
  --jitter 0.3
echo ""

echo "9. Multiple compression formats"
echo "-----------------------------"
for compression in gzip bz2 lzma; do
  echo "  Generating with $compression compression..."
  logsmith generate \
    --count 5000 \
    --format json \
    --output examples/output/compressed_${compression}.json \
    --compression $compression
done
echo ""

echo "10. Configuration file example"
echo "-----------------------------"
# Create a configuration file
cat > examples/output/example_config.json << EOF
{
  "total_logs": 15000,
  "log_levels": ["DEBUG", "INFO", "WARNING", "ERROR"],
  "level_distribution": {
    "levels": {
      "DEBUG": 0.2,
      "INFO": 0.6,
      "WARNING": 0.15,
      "ERROR": 0.05
    }
  },
  "output": {
    "format": "json",
    "file_path": "examples/output/config_based.json",
    "compression": "gzip"
  },
  "performance": {
    "batch_size": 5000,
    "workers": 2
  },
  "custom_fields": {
    "service": "example-service",
    "version": "2.0.0",
    "datacenter": "us-west-2"
  }
}
EOF

logsmith generate --config examples/output/example_config.json
echo ""

echo "11. Validation and initialization"
echo "--------------------------------"
# Initialize a new config
logsmith init-config --output examples/output/new_config.json --format apache_common --count 50000

# Validate the config
logsmith validate-config examples/output/new_config.json
echo ""

echo "12. List available formats"
echo "-------------------------"
logsmith list-formats
echo ""

echo "13. Performance benchmark"
echo "-----------------------"
logsmith benchmark --count 50000 --format json --iterations 3
echo ""

echo "14. Large dataset with progress"
echo "-----------------------------"
logsmith generate \
  --count 200000 \
  --format json \
  --output examples/output/large_dataset.json \
  --workers 4 \
  --batch-size 20000
echo ""

echo "15. GELF format for Graylog"
echo "--------------------------"
logsmith generate \
  --count 5000 \
  --format gelf \
  --output examples/output/graylog.json \
  --custom-fields '{"facility": "app", "host": "server01"}'
echo ""

echo "16. CEF format for security"
echo "--------------------------"
logsmith generate \
  --count 3000 \
  --format cef \
  --output examples/output/security.log \
  --level-dist '{"WARNING": 0.6, "ERROR": 0.3, "CRITICAL": 0.1}'
echo ""

echo "All CLI examples completed!"
echo "Check the examples/output/ directory for generated files."
echo ""
echo "File sizes:"
ls -lh examples/output/ | grep -v "^d"