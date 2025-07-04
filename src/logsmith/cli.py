"""Command-line interface for LogSmith."""

import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
import multiprocessing as mp

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from logsmith.core.config import LogConfig
from logsmith.core.generator import LogGenerator
from logsmith.core.formats import FormatterFactory
from logsmith.utils.performance import BenchmarkRunner, ProgressReporter


class SafeConsole:
    """A safe console wrapper that handles test environments."""
    
    def __init__(self):
        self._console = None
        self._init_console()
    
    def _init_console(self):
        """Initialize the console if possible."""
        try:
            self._console = Console()
        except Exception:
            self._console = None
    
    def print(self, *args, **kwargs):
        """Print with fallback to regular print."""
        if self._console:
            try:
                self._console.print(*args, **kwargs)
            except (ValueError, OSError, AttributeError):
                # Fallback to regular print
                try:
                    # Remove Rich-specific styling for basic print
                    cleaned_args = []
                    for arg in args:
                        if hasattr(arg, '__rich__') or hasattr(arg, '__rich_console__'):
                            # Convert Rich objects to plain text
                            cleaned_args.append(str(arg).replace('\n', ' '))
                        else:
                            cleaned_args.append(arg)
                    print(*cleaned_args)
                except (ValueError, OSError):
                    # Silently fail if stdout is closed
                    pass
        else:
            try:
                # Remove Rich-specific styling for basic print
                cleaned_args = []
                for arg in args:
                    if hasattr(arg, '__rich__') or hasattr(arg, '__rich_console__'):
                        # Convert Rich objects to plain text
                        cleaned_args.append(str(arg).replace('\n', ' '))
                    else:
                        cleaned_args.append(arg)
                print(*cleaned_args)
            except (ValueError, OSError):
                # Silently fail if stdout is closed
                pass

console = SafeConsole()


def validate_format(ctx, param, value):
    """Validate log format."""
    try:
        available_formats = FormatterFactory.get_available_formats()
        if value not in available_formats:
            raise click.BadParameter(f"Invalid format. Available: {', '.join(available_formats)}")
        return value
    except Exception as e:
        raise click.BadParameter(str(e))


def validate_positive_int(ctx, param, value):
    """Validate positive integer."""
    if value <= 0:
        raise click.BadParameter("Must be a positive integer")
    return value


def validate_file_path(ctx, param, value):
    """Validate file path."""
    if value:
        path = Path(value)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            return path
        except Exception as e:
            raise click.BadParameter(f"Invalid file path: {e}")
    return value


@click.group()
@click.version_option()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, verbose):
    """LogSmith - High-performance log generator for testing and simulation."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose


@cli.command()
@click.option('--count', '-c', default=1000, callback=validate_positive_int,
              help='Number of logs to generate')
@click.option('--format', '-f', default='standard', callback=validate_format,
              help='Log format (standard, json, apache_common, etc.)')
@click.option('--output', '-o', callback=validate_file_path,
              help='Output file path (default: stdout)')
@click.option('--start-time', help='Start time (ISO format)')
@click.option('--end-time', help='End time (ISO format)')
@click.option('--duration', help='Duration (e.g., 1h, 30m, 24h)')
@click.option('--interval', default=1.0, help='Base interval between logs (seconds)')
@click.option('--jitter', default=0.1, help='Timestamp jitter factor (0-1)')
@click.option('--batch-size', default=10000, callback=validate_positive_int,
              help='Batch size for processing')
@click.option('--workers', type=int, help='Number of worker processes')
@click.option('--compression', type=click.Choice(['gzip', 'bz2', 'lzma']),
              help='Compression format')
@click.option('--config', help='Configuration file path')
@click.option('--level-dist', help='Log level distribution (JSON string)')
@click.option('--message-templates', help='Message templates file path')
@click.option('--custom-fields', help='Custom fields (JSON string)')
@click.option('--seed', type=int, help='Random seed for deterministic generation')
@click.option('--anomalies', is_flag=True, help='Enable anomaly injection')
@click.option('--anomaly-rate', type=float, help='Base anomaly rate (0.0-1.0)')
@click.option('--anomaly-config', help='Anomaly configuration file path')
@click.option('--no-progress', is_flag=True, help='Disable progress bar')
@click.option('--benchmark', is_flag=True, help='Run in benchmark mode')
@click.option('--validate-only', is_flag=True, help='Only validate configuration')
@click.pass_context
def generate(ctx, count, format, output, start_time, end_time, duration, interval,
             jitter, batch_size, workers, compression, config, level_dist,
             message_templates, custom_fields, seed, anomalies, anomaly_rate,
             anomaly_config, no_progress, benchmark, validate_only):
    """Generate logs with specified parameters."""
    
    try:
        # Load configuration
        if config:
            log_config = LogConfig.from_file(config)
        else:
            log_config = LogConfig()
        
        # Override with CLI parameters
        if count != 1000:
            log_config.total_logs = count
        
        if format != 'standard':
            log_config.output.format = format
        
        if output:
            log_config.output.file_path = output
        
        if compression:
            log_config.output.compression = compression
        
        if batch_size != 10000:
            log_config.performance.batch_size = batch_size
        
        if workers:
            log_config.performance.workers = workers
        
        if interval != 1.0:
            log_config.time.interval = interval
        
        if jitter != 0.1:
            log_config.time.jitter = jitter
        
        # Parse duration
        if duration:
            log_config.time.duration = _parse_duration(duration)
        
        # Parse custom fields
        if custom_fields:
            try:
                log_config.custom_fields = json.loads(custom_fields)
            except json.JSONDecodeError:
                raise click.BadParameter("Invalid JSON for custom fields")
        
        # Parse level distribution
        if level_dist:
            try:
                dist_data = json.loads(level_dist)
                log_config.level_distribution.levels = dist_data
            except json.JSONDecodeError:
                raise click.BadParameter("Invalid JSON for level distribution")
        
        # Load message templates
        if message_templates:
            try:
                with open(message_templates, 'r') as f:
                    templates = json.load(f)
                log_config.message_templates = templates
            except (FileNotFoundError, json.JSONDecodeError) as e:
                raise click.BadParameter(f"Invalid message templates file: {e}")
        
        # Handle seed parameter
        if seed is not None:
            log_config.seed = seed
        
        # Handle anomaly parameters
        if anomalies:
            log_config.anomaly_config.enabled = True
            
        if anomaly_rate is not None:
            if not 0.0 <= anomaly_rate <= 1.0:
                raise click.BadParameter("Anomaly rate must be between 0.0 and 1.0")
            log_config.anomaly_config.base_rate = anomaly_rate
            
        # Load anomaly configuration file
        if anomaly_config:
            try:
                with open(anomaly_config, 'r') as f:
                    anomaly_data = json.load(f)
                # Update anomaly config with file contents
                for key, value in anomaly_data.items():
                    if hasattr(log_config.anomaly_config, key):
                        setattr(log_config.anomaly_config, key, value)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                raise click.BadParameter(f"Invalid anomaly configuration file: {e}")
        
        # Create generator
        generator = LogGenerator(log_config)
        
        # Validate configuration
        warnings = generator.validate_config()
        if warnings and not no_progress:
            console.print(Panel(
                "\n".join(f"⚠️  {w}" for w in warnings),
                title="Configuration Warnings",
                border_style="yellow"
            ))
        
        if validate_only:
            console.print("✅ Configuration is valid")
            return
        
        # Show configuration summary
        verbose = ctx.obj.get('verbose') if ctx.obj else False
        if verbose or benchmark:
            _show_config_summary(log_config)
        
        # Run benchmark if requested
        if benchmark:
            # Default to /dev/null for benchmark mode if no output specified
            if not log_config.output.file_path:
                log_config.output.file_path = '/dev/null'
            _run_benchmark(generator, log_config)
            return
        
        # Generate logs
        if no_progress:
            generator.generate()
        else:
            _generate_with_progress(generator, log_config)
        
        # Show performance stats (only if not outputting to stdout and not no-progress)
        if not no_progress and log_config.output.file_path:
            stats = generator.get_performance_stats()
            if stats.get('duration_seconds', 0) > 0:
                console.print(Panel(
                    _format_performance_stats(stats),
                    title="Performance Statistics",
                    border_style="green"
                ))
    
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        verbose = ctx.obj.get('verbose') if ctx.obj else False
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.option('--count', '-c', default=1000000, help='Number of logs for benchmark')
@click.option('--format', '-f', default='standard', help='Log format to benchmark')
@click.option('--iterations', '-i', default=3, help='Number of benchmark iterations')
@click.option('--workers', type=int, help='Number of worker processes')
@click.option('--output', help='Save benchmark results to file')
@click.option('--log-output', help='Log output file (default: /dev/null)')
def benchmark(count, format, iterations, workers, output, log_output):
    """Run performance benchmarks."""
    
    console.print(f"🚀 Running benchmark with {count:,} logs...")
    
    # Default log output to /dev/null for benchmarks
    if log_output is None:
        log_output = '/dev/null'
    
    # Create benchmark configuration
    config = LogConfig(
        total_logs=count,
        output={"format": format, "file_path": log_output},
        performance={"workers": workers} if workers else {}
    )
    
    # Run benchmark
    results = BenchmarkRunner.run_generation_benchmark(config, iterations)
    
    # Display results
    console.print(Panel(
        BenchmarkRunner.format_benchmark_results(results),
        title="Benchmark Results",
        border_style="green"
    ))
    
    # Save results if requested
    if output:
        with open(output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        console.print(f"📊 Results saved to {output}")


@cli.command()
@click.option('--output', '-o', default='logsmith-config.json',
              help='Output configuration file path')
@click.option('--format', '-f', default='standard',
              help='Default log format')
@click.option('--count', '-c', default=1000,
              help='Default log count')
def init_config(output, format, count):
    """Initialize a configuration file."""
    
    config = LogConfig(
        total_logs=count,
        output={"format": format}
    )
    
    config.to_file(output)
    console.print(f"📝 Configuration file created: {output}")


@cli.command()
@click.argument('config_file')
def validate_config(config_file):
    """Validate a configuration file."""
    
    try:
        config = LogConfig.from_file(config_file)
        generator = LogGenerator(config)
        warnings = generator.validate_config()
        
        if warnings:
            console.print(Panel(
                "\n".join(f"⚠️  {w}" for w in warnings),
                title="Configuration Warnings",
                border_style="yellow"
            ))
        
        console.print("✅ Configuration is valid")
        _show_config_summary(config)
        
    except Exception as e:
        console.print(f"❌ Invalid configuration: {e}", style="red")
        sys.exit(1)


@cli.command()
def list_formats():
    """List available log formats."""
    
    formats = FormatterFactory.get_available_formats()
    
    table = Table(title="Available Log Formats")
    table.add_column("Format", style="cyan")
    table.add_column("Description", style="white")
    
    descriptions = {
        "standard": "Standard timestamp - level - message format",
        "json": "JSON format with structured fields",
        "apache_common": "Apache Common Log Format (CLF)",
        "apache_combined": "Apache Combined Log Format",
        "nginx": "Nginx access log format",
        "syslog": "Syslog RFC3164 format",
        "csv": "Comma-separated values",
        "logfmt": "Logfmt key=value format",
        "gelf": "Graylog Extended Log Format",
        "cef": "Common Event Format",
        "custom": "Custom format with templates"
    }
    
    for fmt in formats:
        table.add_row(fmt, descriptions.get(fmt, "No description available"))
    
    console.print(table)


@cli.command()
@click.argument('log_file')
@click.option('--lines', '-n', default=10, help='Number of lines to analyze')
@click.option('--format', '-f', help='Expected log format')
def analyze(log_file, lines, format):
    """Analyze an existing log file."""
    
    try:
        with open(log_file, 'r') as f:
            sample_lines = [f.readline().strip() for _ in range(lines)]
        
        console.print(f"📊 Analyzing {log_file}...")
        console.print(f"Sample lines: {len([l for l in sample_lines if l])}")
        
        # Basic analysis
        if sample_lines:
            console.print(f"First line: {sample_lines[0]}")
            console.print(f"Average line length: {sum(len(l) for l in sample_lines) / len(sample_lines):.1f}")
        
        # TODO: Add more sophisticated analysis
        
    except Exception as e:
        console.print(f"❌ Error analyzing file: {e}", style="red")
        sys.exit(1)


def _parse_duration(duration_str: str):
    """Parse duration string (e.g., '1h', '30m', '24h')."""
    import re
    from datetime import timedelta
    
    match = re.match(r'^(\d+)([smhd])$', duration_str.lower())
    if not match:
        raise click.BadParameter("Invalid duration format. Use: 5s, 30m, 2h, 1d")
    
    value, unit = match.groups()
    value = int(value)
    
    if unit == 's':
        return timedelta(seconds=value)
    elif unit == 'm':
        return timedelta(minutes=value)
    elif unit == 'h':
        return timedelta(hours=value)
    elif unit == 'd':
        return timedelta(days=value)


def _show_config_summary(config: LogConfig):
    """Show configuration summary."""
    
    table = Table(title="Configuration Summary")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Total logs", f"{config.total_logs:,}")
    table.add_row("Format", config.output.format)
    table.add_row("Output", str(config.output.file_path or "stdout"))
    table.add_row("Batch size", f"{config.performance.batch_size:,}")
    table.add_row("Workers", str(config.performance.workers or "auto"))
    table.add_row("Compression", config.output.compression or "none")
    table.add_row("Interval", str(config.time.interval))
    table.add_row("Jitter", f"{config.time.jitter:.1%}")
    
    console.print(table)


def _generate_with_progress(generator: LogGenerator, config: LogConfig):
    """Generate logs with progress bar."""
    
    try:
        # Use the rich console if available
        rich_console = console._console if console._console else None
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("•"),
            TextColumn("[progress.completed]{task.completed:,}/{task.total:,}"),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=rich_console,
            transient=False
        ) as progress:
            
            task = progress.add_task("Generating logs...", total=config.total_logs)
            
            def progress_callback(percentage: float, logs_generated: int):
                progress.update(task, completed=logs_generated)
                generator.performance_monitor.log_progress(logs_generated)
            
            generator.generate(progress_callback)
    except (ValueError, OSError, AttributeError):
        # Fallback: generate without progress bar if Rich fails
        generator.generate()


def _format_performance_stats(stats: Dict[str, Any]) -> str:
    """Format performance statistics for display."""
    
    lines = [
        f"Duration: {stats['duration_seconds']:.2f} seconds",
        f"Logs generated: {stats['total_logs_generated']:,}",
        f"Logs per second: {stats['logs_per_second']:,.0f}",
        f"Peak memory: {stats['peak_memory_usage_mb']:.1f} MB",
        f"Peak CPU: {stats['peak_cpu_usage_percent']:.1f}%",
    ]
    
    return "\n".join(lines)


def _run_benchmark(generator: LogGenerator, config: LogConfig):
    """Run benchmark mode."""
    
    console.print("🔥 Running in benchmark mode...")
    
    # Estimate time
    estimated_time = generator.estimate_generation_time()
    console.print(f"⏱️  Estimated time: {estimated_time:.2f} seconds")
    
    # Run with progress
    _generate_with_progress(generator, config)
    
    # Show detailed stats
    stats = generator.get_performance_stats()
    console.print(Panel(
        _format_performance_stats(stats),
        title="Benchmark Results",
        border_style="green"
    ))
    
    # Performance evaluation
    target_rate = 250_000  # Realistic target: 250K logs/second
    actual_rate = stats.get('logs_per_second', 0)
    
    if actual_rate >= target_rate:
        console.print("🎯 Performance target achieved!", style="green")
    else:
        console.print(f"📈 Performance: {actual_rate/target_rate:.1%} of target", style="yellow")


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()