"""Anomaly injection system for LogForge."""

import random
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass

from logforge.core.config import (
    AnomalyConfig,
    AnomalyType,
    TemporalPattern,
    AnomalyPatternConfig,
    AnomalyTypeConfig,
)


def parse_duration(duration_str: str) -> timedelta:
    """Parse duration string (e.g., '5m', '1h', '30s')."""
    if not duration_str:
        return timedelta(0)

    match = re.match(r'^(\d+)([smhd])$', duration_str.lower())
    if not match:
        raise ValueError(f"Invalid duration format: {duration_str}")

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
    else:
        raise ValueError(f"Invalid time unit: {unit}")


@dataclass
class AnomalyEvent:
    """Represents a single anomaly event."""

    anomaly_type: AnomalyType
    timestamp: datetime
    severity: float
    metadata: Dict[str, Any]
    correlation_id: Optional[str] = None


class TemporalPatternGenerator:
    """Generates temporal anomaly patterns."""

    def __init__(
        self,
        config: AnomalyPatternConfig,
        start_time: datetime,
        total_duration: timedelta,
    ):
        self.config = config
        self.start_time = start_time
        self.total_duration = total_duration
        self.pattern_start_time = self._calculate_pattern_start_time()
        self.pattern_duration = (
            parse_duration(config.duration) if config.duration else total_duration
        )

    def _calculate_pattern_start_time(self) -> datetime:
        """Calculate when this pattern should start."""
        if self.config.start_time:
            offset = parse_duration(self.config.start_time)
            return self.start_time + offset
        return self.start_time

    def get_anomaly_rate(self, timestamp: datetime) -> float:
        """Get the anomaly rate at a specific timestamp."""
        if not self._is_pattern_active(timestamp):
            return 0.0

        progress = self._get_pattern_progress(timestamp)

        if self.config.pattern_type == TemporalPattern.CONSTANT:
            return self.config.base_rate

        elif self.config.pattern_type == TemporalPattern.BURST:
            peak_rate = self.config.peak_rate or (self.config.base_rate * 10)
            return peak_rate

        elif self.config.pattern_type == TemporalPattern.GRADUAL_INCREASE:
            peak_rate = self.config.peak_rate or (self.config.base_rate * 5)
            return (
                self.config.base_rate + (peak_rate - self.config.base_rate) * progress
            )

        elif self.config.pattern_type == TemporalPattern.GRADUAL_DECREASE:
            peak_rate = self.config.peak_rate or (self.config.base_rate * 5)
            return peak_rate - (peak_rate - self.config.base_rate) * progress

        elif self.config.pattern_type == TemporalPattern.SPIKE:
            # Sharp spike at the middle of the duration
            spike_center = 0.5
            spike_width = 0.1  # 10% of duration
            distance_from_center = abs(progress - spike_center)
            if distance_from_center <= spike_width:
                peak_rate = self.config.peak_rate or (self.config.base_rate * 20)
                spike_intensity = 1.0 - (distance_from_center / spike_width)
                return (
                    self.config.base_rate
                    + (peak_rate - self.config.base_rate) * spike_intensity
                )
            return self.config.base_rate

        elif self.config.pattern_type == TemporalPattern.PERIODIC:
            if self.config.period:
                period_duration = parse_duration(self.config.period)
                cycle_progress = (timestamp - self.pattern_start_time) % period_duration
                cycle_ratio = (
                    cycle_progress.total_seconds() / period_duration.total_seconds()
                )
                # Sine wave pattern
                import math

                intensity = (math.sin(2 * math.pi * cycle_ratio) + 1) / 2
                peak_rate = self.config.peak_rate or (self.config.base_rate * 3)
                return (
                    self.config.base_rate
                    + (peak_rate - self.config.base_rate) * intensity
                )
            return self.config.base_rate

        return self.config.base_rate

    def _is_pattern_active(self, timestamp: datetime) -> bool:
        """Check if the pattern is active at the given timestamp."""
        pattern_end = self.pattern_start_time + self.pattern_duration
        return self.pattern_start_time <= timestamp <= pattern_end

    def _get_pattern_progress(self, timestamp: datetime) -> float:
        """Get progress through the pattern (0.0 to 1.0)."""
        if not self._is_pattern_active(timestamp):
            return 0.0
        elapsed = timestamp - self.pattern_start_time
        return min(elapsed.total_seconds() / self.pattern_duration.total_seconds(), 1.0)


class AnomalyInjector:
    """Main anomaly injection system."""

    def __init__(
        self,
        config: AnomalyConfig,
        log_format: str,
        start_time: datetime,
        total_duration: timedelta,
    ):
        self.config = config
        self.log_format = log_format
        self.start_time = start_time
        self.total_duration = total_duration

        # Initialize random seed for anomalies
        self.anomaly_random = random.Random(config.seed)

        # Initialize temporal pattern generators
        self.pattern_generators = [
            TemporalPatternGenerator(pattern, start_time, total_duration)
            for pattern in config.patterns
        ]

        # Get format-specific anomaly types
        self.relevant_anomaly_types = self._get_relevant_anomaly_types()

        # Correlation tracking
        self.active_correlations: Dict[str, List[AnomalyEvent]] = {}
        self.correlation_counter = 0

    def _get_relevant_anomaly_types(self) -> Set[AnomalyType]:
        """Get anomaly types relevant to the current log format."""
        format_mapping = self.config.format_mappings.get(self.log_format, [])
        configured_types = set(self.config.anomaly_types.keys())

        if format_mapping:
            return set(format_mapping) & configured_types
        return configured_types

    def should_inject_anomaly(self, timestamp: datetime) -> bool:
        """Determine if an anomaly should be injected at this timestamp."""
        if not self.config.enabled:
            return False

        # Calculate combined anomaly rate from all active patterns
        total_rate = self.config.base_rate

        for generator in self.pattern_generators:
            pattern_rate = generator.get_anomaly_rate(timestamp)
            total_rate = max(total_rate, pattern_rate)  # Use highest rate

        return self.anomaly_random.random() < total_rate

    def generate_anomaly(
        self, timestamp: datetime, base_log_data: Dict[str, Any]
    ) -> Optional[AnomalyEvent]:
        """Generate an anomaly event."""
        if not self.should_inject_anomaly(timestamp):
            return None

        # Select anomaly type based on weights and format relevance
        anomaly_type = self._select_anomaly_type(timestamp)
        if not anomaly_type:
            return None

        # Generate severity
        type_config = self.config.anomaly_types.get(anomaly_type, AnomalyTypeConfig())
        severity = self.anomaly_random.uniform(*type_config.severity_range)

        # Generate anomaly metadata
        metadata = self._generate_anomaly_metadata(
            anomaly_type, severity, base_log_data
        )

        # Handle correlation
        correlation_id = self._handle_correlation(anomaly_type, timestamp)

        anomaly = AnomalyEvent(
            anomaly_type=anomaly_type,
            timestamp=timestamp,
            severity=severity,
            metadata=metadata,
            correlation_id=correlation_id,
        )

        # Add to correlation tracking
        if correlation_id:
            self._add_to_correlation(correlation_id, anomaly)

        return anomaly

    def _select_anomaly_type(self, timestamp: datetime) -> Optional[AnomalyType]:
        """Select an anomaly type based on patterns and weights."""
        # Get active patterns for this timestamp
        active_pattern_types = set()
        for generator in self.pattern_generators:
            if generator.get_anomaly_rate(timestamp) > 0:
                active_pattern_types.update(generator.config.anomaly_types)

        # If patterns are active, prefer their anomaly types
        if active_pattern_types:
            candidate_types = active_pattern_types & self.relevant_anomaly_types
        else:
            candidate_types = self.relevant_anomaly_types

        if not candidate_types:
            return None

        # Weight-based selection
        weights = []
        types = list(candidate_types)

        for anomaly_type in types:
            type_config = self.config.anomaly_types.get(
                anomaly_type, AnomalyTypeConfig()
            )
            weights.append(type_config.weight)

        if not weights:
            return None

        return self.anomaly_random.choices(types, weights=weights)[0]

    def _generate_anomaly_metadata(
        self, anomaly_type: AnomalyType, severity: float, base_log_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate metadata for specific anomaly types."""
        metadata = {"severity": severity}

        if anomaly_type == AnomalyType.HIGH_LATENCY:
            # Normal latency: 50-500ms, anomalous: 1000-30000ms
            base_latency = 100
            anomaly_latency = base_latency + (severity * 29000)
            metadata.update(
                {
                    "response_time": int(anomaly_latency),
                    "normal_response_time": base_latency,
                    "anomaly_multiplier": anomaly_latency / base_latency,
                }
            )

        elif anomaly_type == AnomalyType.MEMORY_SPIKE:
            # Normal: 10-70%, anomalous: 80-99%
            normal_memory = self.anomaly_random.uniform(10, 70)
            anomaly_memory = 80 + (severity * 19)
            metadata.update(
                {
                    "memory_usage": round(anomaly_memory, 2),
                    "normal_memory": round(normal_memory, 2),
                    "memory_threshold": 80.0,
                }
            )

        elif anomaly_type == AnomalyType.CPU_SPIKE:
            normal_cpu = self.anomaly_random.uniform(5, 60)
            anomaly_cpu = 70 + (severity * 30)
            metadata.update(
                {
                    "cpu_usage": round(anomaly_cpu, 2),
                    "normal_cpu": round(normal_cpu, 2),
                    "cpu_threshold": 70.0,
                }
            )

        elif anomaly_type == AnomalyType.FAILED_AUTH:
            metadata.update(
                {
                    "failed_attempts": int(1 + severity * 20),
                    "auth_method": self.anomaly_random.choice(
                        ["password", "token", "certificate", "oauth"]
                    ),
                    "source_ip": self._generate_suspicious_ip(),
                    "user_agent": self._generate_suspicious_user_agent(),
                }
            )

        elif anomaly_type == AnomalyType.BRUTE_FORCE:
            metadata.update(
                {
                    "attempt_count": int(10 + severity * 100),
                    "time_window": "5m",
                    "target_accounts": self.anomaly_random.randint(1, 10),
                    "source_ip": self._generate_suspicious_ip(),
                }
            )

        elif anomaly_type == AnomalyType.SUSPICIOUS_ACCESS:
            metadata.update(
                {
                    "access_pattern": self.anomaly_random.choice(
                        [
                            "unusual_time",
                            "unusual_location",
                            "privilege_escalation",
                            "data_enumeration",
                            "lateral_movement",
                        ]
                    ),
                    "risk_score": severity,
                    "source_ip": self._generate_suspicious_ip(),
                }
            )

        elif anomaly_type == AnomalyType.SERVICE_UNAVAILABLE:
            metadata.update(
                {
                    "service_name": self.anomaly_random.choice(
                        [
                            "database",
                            "cache",
                            "auth_service",
                            "payment_api",
                            "notification_service",
                            "file_storage",
                        ]
                    ),
                    "error_rate": round(severity * 100, 2),
                    "downtime_duration": int(severity * 3600),  # up to 1 hour
                }
            )

        elif anomaly_type == AnomalyType.UNUSUAL_VOLUME:
            normal_volume = self.anomaly_random.randint(100, 1000)
            anomaly_volume = int(normal_volume * (1 + severity * 10))
            metadata.update(
                {
                    "request_volume": anomaly_volume,
                    "normal_volume": normal_volume,
                    "volume_multiplier": anomaly_volume / normal_volume,
                }
            )

        return metadata

    def _generate_suspicious_ip(self) -> str:
        """Generate suspicious IP addresses."""
        suspicious_ranges = [
            "10.0.0.{}",
            "192.168.1.{}",
            "172.16.0.{}",  # Internal scanning
            "1.1.1.{}",
            "8.8.8.{}",
            "208.67.222.{}",  # Known proxies/DNS
            "185.220.{}.{}",
            "199.87.{}.{}",  # Known malicious ranges
        ]
        range_template = self.anomaly_random.choice(suspicious_ranges)

        if "{}.{}" in range_template:
            return range_template.format(
                self.anomaly_random.randint(1, 254), self.anomaly_random.randint(1, 254)
            )
        else:
            return range_template.format(self.anomaly_random.randint(1, 254))

    def _generate_suspicious_user_agent(self) -> str:
        """Generate suspicious user agents."""
        suspicious_agents = [
            "curl/7.68.0",
            "wget/1.20.3",
            "python-requests/2.25.1",
            "sqlmap/1.4.9",
            "Nmap Scripting Engine",
            "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)",  # Very old
            "Bot/1.0",
            "Scanner/1.0",
        ]
        return self.anomaly_random.choice(suspicious_agents)

    def _handle_correlation(
        self, anomaly_type: AnomalyType, timestamp: datetime
    ) -> Optional[str]:
        """Handle anomaly correlation."""
        if self.anomaly_random.random() > self.config.correlation_probability:
            return None

        # Check for existing correlations within the time window
        correlation_window = parse_duration(self.config.correlation_window)

        for correlation_id, events in self.active_correlations.items():
            if events and (timestamp - events[-1].timestamp) <= correlation_window:
                # Add to existing correlation
                return correlation_id

        # Create new correlation
        self.correlation_counter += 1
        correlation_id = f"corr_{self.correlation_counter:04d}"
        self.active_correlations[correlation_id] = []
        return correlation_id

    def _add_to_correlation(self, correlation_id: str, anomaly: AnomalyEvent) -> None:
        """Add an anomaly to a correlation group."""
        if correlation_id and correlation_id in self.active_correlations:
            self.active_correlations[correlation_id].append(anomaly)

    def apply_anomaly_to_log(
        self, log_data: Dict[str, Any], anomaly: AnomalyEvent
    ) -> Dict[str, Any]:
        """Apply anomaly modifications to log data."""
        modified_log = log_data.copy()

        # Add anomaly metadata
        modified_log["anomaly"] = {
            "type": anomaly.anomaly_type.value,
            "severity": anomaly.severity,
            "correlation_id": anomaly.correlation_id,
            **anomaly.metadata,
        }

        # Apply format-specific modifications
        if self.log_format in ["apache_common", "apache_combined"]:
            modified_log = self._apply_apache_anomaly(modified_log, anomaly)
        elif self.log_format == "json":
            modified_log = self._apply_json_anomaly(modified_log, anomaly)
        elif self.log_format == "syslog":
            modified_log = self._apply_syslog_anomaly(modified_log, anomaly)

        return modified_log

    def _apply_apache_anomaly(
        self, log_data: Dict[str, Any], anomaly: AnomalyEvent
    ) -> Dict[str, Any]:
        """Apply anomaly modifications for Apache logs."""
        if anomaly.anomaly_type == AnomalyType.FAILED_AUTH:
            log_data["status_code"] = 401
            log_data["user"] = "-"  # Failed auth shows no user

        elif anomaly.anomaly_type == AnomalyType.BRUTE_FORCE:
            log_data["status_code"] = 401
            log_data["ip"] = anomaly.metadata.get("source_ip", log_data.get("ip"))

        elif anomaly.anomaly_type == AnomalyType.SERVICE_UNAVAILABLE:
            log_data["status_code"] = self.anomaly_random.choice([500, 502, 503, 504])
            log_data["response_size"] = 0

        elif anomaly.anomaly_type == AnomalyType.SUSPICIOUS_ACCESS:
            log_data["ip"] = anomaly.metadata.get("source_ip", log_data.get("ip"))
            log_data["method"] = self.anomaly_random.choice(["POST", "PUT", "DELETE"])
            log_data["url"] = self.anomaly_random.choice(
                ["/admin", "/config", "/backup", "/.env", "/wp-admin"]
            )

        return log_data

    def _apply_json_anomaly(
        self, log_data: Dict[str, Any], anomaly: AnomalyEvent
    ) -> Dict[str, Any]:
        """Apply anomaly modifications for JSON logs."""
        if anomaly.anomaly_type == AnomalyType.HIGH_LATENCY:
            log_data["response_time"] = anomaly.metadata["response_time"]
            log_data["level"] = "WARNING"

        elif anomaly.anomaly_type == AnomalyType.MEMORY_SPIKE:
            log_data["memory_usage"] = anomaly.metadata["memory_usage"]
            log_data["level"] = "ERROR" if anomaly.severity > 0.8 else "WARNING"

        elif anomaly.anomaly_type == AnomalyType.CPU_SPIKE:
            log_data["cpu_usage"] = anomaly.metadata["cpu_usage"]
            log_data["level"] = "ERROR" if anomaly.severity > 0.8 else "WARNING"

        return log_data

    def _apply_syslog_anomaly(
        self, log_data: Dict[str, Any], anomaly: AnomalyEvent
    ) -> Dict[str, Any]:
        """Apply anomaly modifications for Syslog."""
        if anomaly.anomaly_type == AnomalyType.PRIVILEGE_ESCALATION:
            log_data["facility"] = "authpriv"
            log_data["level"] = "ERROR"
            log_data["process"] = "sudo"

        elif anomaly.anomaly_type == AnomalyType.FAILED_AUTH:
            log_data["facility"] = "authpriv"
            log_data["level"] = "WARNING"
            log_data["process"] = "sshd"

        return log_data
