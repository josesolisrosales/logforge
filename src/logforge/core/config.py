"""Configuration management for LogForge."""

import json
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator
from pydantic.types import PositiveInt


class AnomalyType(str, Enum):
    """Available anomaly types."""

    # Security anomalies
    FAILED_AUTH = "failed_auth"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    SUSPICIOUS_ACCESS = "suspicious_access"
    DATA_EXFILTRATION = "data_exfiltration"
    BRUTE_FORCE = "brute_force"
    INJECTION_ATTACK = "injection_attack"

    # Performance anomalies
    HIGH_LATENCY = "high_latency"
    MEMORY_SPIKE = "memory_spike"
    CPU_SPIKE = "cpu_spike"
    SLOW_QUERY = "slow_query"
    TIMEOUT_CASCADE = "timeout_cascade"
    RESOURCE_EXHAUSTION = "resource_exhaustion"

    # System failures
    SERVICE_UNAVAILABLE = "service_unavailable"
    DATABASE_ERROR = "database_error"
    NETWORK_ERROR = "network_error"
    DISK_FULL = "disk_full"

    # Behavioral anomalies
    UNUSUAL_VOLUME = "unusual_volume"
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"
    TIME_ANOMALY = "time_anomaly"
    USER_BEHAVIOR = "user_behavior"


class TemporalPattern(str, Enum):
    """Temporal anomaly patterns."""

    CONSTANT = "constant"
    BURST = "burst"
    GRADUAL_INCREASE = "gradual_increase"
    GRADUAL_DECREASE = "gradual_decrease"
    PERIODIC = "periodic"
    SPIKE = "spike"


class AnomalyPatternConfig(BaseModel):
    """Configuration for a specific anomaly pattern."""

    pattern_type: TemporalPattern = Field(description="Type of temporal pattern")
    anomaly_types: List[AnomalyType] = Field(
        description="Anomaly types to inject during this pattern"
    )
    base_rate: float = Field(
        default=0.05, ge=0.0, le=1.0, description="Base anomaly rate (0-1)"
    )
    peak_rate: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Peak anomaly rate for bursts/spikes"
    )
    duration: Optional[str] = Field(
        default=None, description="Duration of pattern (e.g., '5m', '1h', '30s')"
    )
    start_time: Optional[str] = Field(
        default=None, description="Start time offset (e.g., '10m', '1h')"
    )
    period: Optional[str] = Field(
        default=None, description="Period for periodic patterns (e.g., '1h', '1d')"
    )

    @validator("peak_rate")
    def validate_peak_rate(cls, v, values):
        if v is not None and "base_rate" in values:
            if v < values["base_rate"]:
                raise ValueError("Peak rate must be >= base rate")
        return v


class AnomalyTypeConfig(BaseModel):
    """Configuration for specific anomaly types."""

    weight: float = Field(
        default=1.0, ge=0.0, description="Relative weight for this anomaly type"
    )
    severity_range: tuple[float, float] = Field(
        default=(0.1, 1.0), description="Severity range (0-1) for this anomaly type"
    )
    format_specific: Dict[str, Any] = Field(
        default_factory=dict, description="Format-specific configuration"
    )
    correlation_groups: List[str] = Field(
        default_factory=list, description="Correlation groups this anomaly belongs to"
    )


class AnomalyConfig(BaseModel):
    """Comprehensive anomaly configuration."""

    enabled: bool = Field(default=False, description="Enable anomaly injection")
    seed: Optional[int] = Field(
        default=None, description="Random seed for anomaly generation"
    )
    base_rate: float = Field(
        default=0.05, ge=0.0, le=1.0, description="Base anomaly rate across all logs"
    )

    # Temporal patterns
    patterns: List[AnomalyPatternConfig] = Field(
        default_factory=list, description="Temporal anomaly patterns to inject"
    )

    # Anomaly type configuration
    anomaly_types: Dict[AnomalyType, AnomalyTypeConfig] = Field(
        default_factory=lambda: {
            AnomalyType.FAILED_AUTH: AnomalyTypeConfig(weight=0.3),
            AnomalyType.BRUTE_FORCE: AnomalyTypeConfig(weight=0.25),
            AnomalyType.SUSPICIOUS_ACCESS: AnomalyTypeConfig(weight=0.2),
            AnomalyType.HIGH_LATENCY: AnomalyTypeConfig(weight=0.2),
            AnomalyType.MEMORY_SPIKE: AnomalyTypeConfig(weight=0.2),
            AnomalyType.UNUSUAL_VOLUME: AnomalyTypeConfig(weight=0.15),
            AnomalyType.SERVICE_UNAVAILABLE: AnomalyTypeConfig(weight=0.15),
            AnomalyType.CPU_SPIKE: AnomalyTypeConfig(weight=0.15),
            AnomalyType.SLOW_QUERY: AnomalyTypeConfig(weight=0.1),
            AnomalyType.DATABASE_ERROR: AnomalyTypeConfig(weight=0.1),
            AnomalyType.USER_BEHAVIOR: AnomalyTypeConfig(weight=0.1),
        },
        description="Configuration for each anomaly type",
    )

    # Format-specific mappings
    format_mappings: Dict[str, List[AnomalyType]] = Field(
        default_factory=lambda: {
            "apache_common": [
                AnomalyType.FAILED_AUTH,
                AnomalyType.BRUTE_FORCE,
                AnomalyType.SUSPICIOUS_ACCESS,
                AnomalyType.SERVICE_UNAVAILABLE,
                AnomalyType.UNUSUAL_VOLUME,
            ],
            "apache_combined": [
                AnomalyType.FAILED_AUTH,
                AnomalyType.BRUTE_FORCE,
                AnomalyType.SUSPICIOUS_ACCESS,
                AnomalyType.SERVICE_UNAVAILABLE,
                AnomalyType.UNUSUAL_VOLUME,
                AnomalyType.GEOGRAPHIC_ANOMALY,
            ],
            "json": [
                AnomalyType.HIGH_LATENCY,
                AnomalyType.MEMORY_SPIKE,
                AnomalyType.CPU_SPIKE,
                AnomalyType.SLOW_QUERY,
                AnomalyType.DATABASE_ERROR,
                AnomalyType.USER_BEHAVIOR,
            ],
            "syslog": [
                AnomalyType.PRIVILEGE_ESCALATION,
                AnomalyType.FAILED_AUTH,
                AnomalyType.SERVICE_UNAVAILABLE,
                AnomalyType.RESOURCE_EXHAUSTION,
                AnomalyType.NETWORK_ERROR,
            ],
        },
        description="Anomaly types relevant to each log format",
    )

    # Correlation configuration
    correlation_probability: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Probability of correlated anomalies occurring together",
    )

    correlation_window: str = Field(
        default="5m", description="Time window for anomaly correlation"
    )

    @validator("base_rate")
    def validate_base_rate(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Base rate must be between 0 and 1")
        return v


class LogLevelDistribution(BaseModel):
    """Log level frequency distribution."""

    levels: Dict[str, float] = Field(
        default={
            "DEBUG": 0.25,
            "INFO": 0.60,
            "WARNING": 0.12,
            "ERROR": 0.025,
            "CRITICAL": 0.005,
        },
        description="Distribution of log levels as probabilities",
    )

    @validator("levels")
    def validate_distribution(cls, v):
        total = sum(v.values())
        if not (0.99 <= total <= 1.01):  # Allow small floating point errors
            raise ValueError(f"Log level probabilities must sum to 1.0, got {total}")
        return v


class TimeConfig(BaseModel):
    """Time-related configuration."""

    start_time: Optional[datetime] = Field(
        default=None,
        description="Start time for log generation (defaults to now - duration)",
    )
    end_time: Optional[datetime] = Field(
        default=None, description="End time for log generation (defaults to now)"
    )
    duration: Optional[timedelta] = Field(
        default_factory=lambda: timedelta(days=1),
        description="Duration of log generation",
    )
    interval: Union[float, str] = Field(
        default=1.0, description="Base interval between logs (seconds) or distribution"
    )
    jitter: float = Field(
        default=0.1, ge=0.0, le=1.0, description="Timestamp jitter factor (0-1)"
    )

    @validator("interval")
    def validate_interval(cls, v):
        if isinstance(v, str):
            allowed_distributions = ["uniform", "normal", "exponential", "poisson"]
            if v not in allowed_distributions:
                raise ValueError(f"Invalid distribution: {v}")
        elif isinstance(v, (int, float)):
            if v <= 0:
                raise ValueError("Interval must be positive")
        return v


class OutputConfig(BaseModel):
    """Output configuration."""

    file_path: Optional[Path] = Field(
        default=None, description="Output file path (None for stdout)"
    )
    format: str = Field(
        default="standard",
        description="Log format (standard, json, apache, nginx, syslog, etc.)",
    )
    compression: Optional[str] = Field(
        default=None, description="Compression format (gzip, bz2, lzma)"
    )
    buffer_size: PositiveInt = Field(
        default=65536, description="Buffer size for batch writing"
    )
    max_file_size: Optional[PositiveInt] = Field(
        default=None, description="Maximum file size before rotation (bytes)"
    )
    rotation_count: PositiveInt = Field(
        default=5, description="Number of rotated files to keep"
    )


class PerformanceConfig(BaseModel):
    """Performance-related configuration."""

    batch_size: PositiveInt = Field(
        default=10000, description="Number of logs to generate in each batch"
    )
    workers: Optional[PositiveInt] = Field(
        default=None, description="Number of worker processes (None for auto-detect)"
    )
    memory_limit: Optional[PositiveInt] = Field(
        default=None, description="Memory limit per worker in MB"
    )
    use_numpy: bool = Field(
        default=True, description="Use numpy for faster array operations"
    )
    precompute_timestamps: bool = Field(
        default=True, description="Pre-compute timestamps for better performance"
    )


class LogConfig(BaseModel):
    """Main configuration class for LogForge."""

    # Core settings
    total_logs: PositiveInt = Field(
        default=1000, description="Total number of logs to generate"
    )
    seed: Optional[int] = Field(
        default=None, description="Random seed for deterministic generation"
    )
    log_levels: List[str] = Field(
        default=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        description="Available log levels",
    )
    level_distribution: LogLevelDistribution = Field(
        default_factory=LogLevelDistribution, description="Log level distribution"
    )

    # Time configuration
    time: TimeConfig = Field(
        default_factory=TimeConfig, description="Time-related settings"
    )

    # Output configuration
    output: OutputConfig = Field(
        default_factory=OutputConfig, description="Output settings"
    )

    # Performance configuration
    performance: PerformanceConfig = Field(
        default_factory=PerformanceConfig, description="Performance settings"
    )

    # Custom fields
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict, description="Custom fields to include in logs"
    )

    # Template configuration
    message_templates: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "DEBUG": ["Debug message: {operation} completed", "Debugging {component}"],
            "INFO": ["User {user_id} logged in", "Processing {item_count} items"],
            "WARNING": [
                "High memory usage: {memory_percent}%",
                "Slow query: {query_time}ms",
            ],
            "ERROR": ["Failed to process {item_id}", "Connection timeout to {host}"],
            "CRITICAL": ["System overload", "Database connection failed"],
        },
        description="Message templates for each log level",
    )

    # Anomaly configuration
    anomaly_config: AnomalyConfig = Field(
        default_factory=AnomalyConfig, description="Anomaly injection configuration"
    )

    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> "LogConfig":
        """Load configuration from a JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(path, 'r') as f:
            data = json.load(f)

        return cls(**data)

    def to_file(self, file_path: Union[str, Path]) -> None:
        """Save configuration to a JSON file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            json.dump(self.dict(), f, indent=2, default=str)

    def get_logs_per_second(self) -> float:
        """Calculate target logs per second."""
        if isinstance(self.time.interval, str):
            return 1.0  # Base rate for distributions
        return 1.0 / self.time.interval

    def get_total_duration(self) -> timedelta:
        """Get total generation duration."""
        if self.time.start_time and self.time.end_time:
            return self.time.end_time - self.time.start_time
        return self.time.duration or timedelta(days=1)

    def get_effective_start_time(self) -> datetime:
        """Get effective start time."""
        if self.time.start_time:
            return self.time.start_time
        end_time = self.time.end_time or datetime.now()
        duration = self.time.duration or timedelta(days=1)
        return end_time - duration

    def get_effective_end_time(self) -> datetime:
        """Get effective end time."""
        if self.time.end_time:
            return self.time.end_time
        start_time = self.time.start_time or datetime.now()
        duration = self.time.duration or timedelta(days=1)
        return start_time + duration
