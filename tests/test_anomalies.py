"""Tests for anomaly injection system."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from logforge.core.config import (
    AnomalyConfig,
    AnomalyPatternConfig,
    AnomalyType,
    TemporalPattern,
)
from logforge.generators.anomalies import (
    AnomalyEvent,
    AnomalyInjector,
    TemporalPatternGenerator,
    parse_duration,
)


class TestParseDuration:
    """Test duration parsing utility."""

    def test_parse_seconds(self):
        """Test parsing seconds."""
        assert parse_duration("30s") == timedelta(seconds=30)
        assert parse_duration("5s") == timedelta(seconds=5)

    def test_parse_minutes(self):
        """Test parsing minutes."""
        assert parse_duration("5m") == timedelta(minutes=5)
        assert parse_duration("30m") == timedelta(minutes=30)

    def test_parse_hours(self):
        """Test parsing hours."""
        assert parse_duration("2h") == timedelta(hours=2)
        assert parse_duration("24h") == timedelta(hours=24)

    def test_parse_days(self):
        """Test parsing days."""
        assert parse_duration("1d") == timedelta(days=1)
        assert parse_duration("7d") == timedelta(days=7)

    def test_parse_empty(self):
        """Test parsing empty string."""
        assert parse_duration("") == timedelta(0)
        assert parse_duration(None) == timedelta(0)

    def test_invalid_format(self):
        """Test invalid duration format."""
        with pytest.raises(ValueError):
            parse_duration("invalid")

        with pytest.raises(ValueError):
            parse_duration("5x")  # Invalid unit


class TestTemporalPatternGenerator:
    """Test temporal pattern generation."""

    def setup_method(self):
        """Setup test fixtures."""
        self.start_time = datetime(2023, 1, 1, 12, 0, 0)
        self.total_duration = timedelta(hours=1)

    def test_constant_pattern(self):
        """Test constant anomaly rate pattern."""
        config = AnomalyPatternConfig(
            pattern_type=TemporalPattern.CONSTANT,
            anomaly_types=[AnomalyType.FAILED_AUTH],
            base_rate=0.1,
        )

        generator = TemporalPatternGenerator(
            config, self.start_time, self.total_duration
        )

        # Rate should be constant throughout
        test_time = self.start_time + timedelta(minutes=30)
        rate = generator.get_anomaly_rate(test_time)
        assert rate == 0.1

        test_time = self.start_time + timedelta(minutes=50)
        rate = generator.get_anomaly_rate(test_time)
        assert rate == 0.1

    def test_burst_pattern(self):
        """Test burst anomaly pattern."""
        config = AnomalyPatternConfig(
            pattern_type=TemporalPattern.BURST,
            anomaly_types=[AnomalyType.BRUTE_FORCE],
            base_rate=0.05,
            peak_rate=0.5,
            duration="10m",
        )

        generator = TemporalPatternGenerator(
            config, self.start_time, self.total_duration
        )

        # During burst period
        test_time = self.start_time + timedelta(minutes=5)
        rate = generator.get_anomaly_rate(test_time)
        assert rate == 0.5  # Peak rate during burst

        # After burst period
        test_time = self.start_time + timedelta(minutes=15)
        rate = generator.get_anomaly_rate(test_time)
        assert rate == 0.0  # Outside pattern window

    def test_gradual_increase_pattern(self):
        """Test gradual increase pattern."""
        config = AnomalyPatternConfig(
            pattern_type=TemporalPattern.GRADUAL_INCREASE,
            anomaly_types=[AnomalyType.HIGH_LATENCY],
            base_rate=0.1,
            peak_rate=0.5,
            duration="20m",
        )

        generator = TemporalPatternGenerator(
            config, self.start_time, self.total_duration
        )

        # At start
        rate_start = generator.get_anomaly_rate(self.start_time)
        assert rate_start == 0.1

        # At middle (should be between base and peak)
        test_time = self.start_time + timedelta(minutes=10)
        rate_middle = generator.get_anomaly_rate(test_time)
        assert 0.1 < rate_middle < 0.5

        # At end
        test_time = self.start_time + timedelta(minutes=20)
        rate_end = generator.get_anomaly_rate(test_time)
        assert rate_end == 0.5

    def test_spike_pattern(self):
        """Test spike pattern."""
        config = AnomalyPatternConfig(
            pattern_type=TemporalPattern.SPIKE,
            anomaly_types=[AnomalyType.MEMORY_SPIKE],
            base_rate=0.05,
            peak_rate=1.0,
            duration="10m",
        )

        generator = TemporalPatternGenerator(
            config, self.start_time, self.total_duration
        )

        # At spike center (5 minutes into 10-minute duration)
        test_time = self.start_time + timedelta(minutes=5)
        rate_center = generator.get_anomaly_rate(test_time)
        assert rate_center > 0.5  # Should be high at center

        # Near edges
        test_time = self.start_time + timedelta(minutes=1)
        rate_edge = generator.get_anomaly_rate(test_time)
        assert rate_edge < rate_center  # Should be lower at edges

    def test_periodic_pattern(self):
        """Test periodic pattern."""
        config = AnomalyPatternConfig(
            pattern_type=TemporalPattern.PERIODIC,
            anomaly_types=[AnomalyType.CPU_SPIKE],
            base_rate=0.1,
            peak_rate=0.4,
            period="10m",
        )

        generator = TemporalPatternGenerator(
            config, self.start_time, self.total_duration
        )

        # Test at different points in cycle
        rates = []
        for minutes in [0, 2, 5, 7, 10]:
            test_time = self.start_time + timedelta(minutes=minutes)
            rate = generator.get_anomaly_rate(test_time)
            rates.append(rate)

        # Should have variation due to sine wave
        assert min(rates) < max(rates)
        assert all(0.1 <= rate <= 0.4 for rate in rates)

    def test_pattern_with_start_offset(self):
        """Test pattern with start time offset."""
        config = AnomalyPatternConfig(
            pattern_type=TemporalPattern.CONSTANT,
            anomaly_types=[AnomalyType.FAILED_AUTH],
            base_rate=0.2,
            start_time="10m",
            duration="10m",
        )

        generator = TemporalPatternGenerator(
            config, self.start_time, self.total_duration
        )

        # Before pattern starts
        test_time = self.start_time + timedelta(minutes=5)
        rate = generator.get_anomaly_rate(test_time)
        assert rate == 0.0

        # During pattern
        test_time = self.start_time + timedelta(minutes=15)
        rate = generator.get_anomaly_rate(test_time)
        assert rate == 0.2

        # After pattern ends
        test_time = self.start_time + timedelta(minutes=25)
        rate = generator.get_anomaly_rate(test_time)
        assert rate == 0.0


class TestAnomalyInjector:
    """Test anomaly injection system."""

    def setup_method(self):
        """Setup test fixtures."""
        self.start_time = datetime(2023, 1, 1, 12, 0, 0)
        self.total_duration = timedelta(hours=1)
        self.config = AnomalyConfig(enabled=True, seed=42, base_rate=0.1)

    def test_init(self):
        """Test injector initialization."""
        injector = AnomalyInjector(
            self.config, "json", self.start_time, self.total_duration
        )

        assert injector.config == self.config
        assert injector.log_format == "json"
        assert injector.start_time == self.start_time
        assert injector.total_duration == self.total_duration
        assert len(injector.pattern_generators) == 0  # No patterns in basic config

    def test_disabled_injection(self):
        """Test that disabled config doesn't inject anomalies."""
        config = AnomalyConfig(enabled=False)
        injector = AnomalyInjector(config, "json", self.start_time, self.total_duration)

        timestamp = self.start_time + timedelta(minutes=30)
        should_inject = injector.should_inject_anomaly(timestamp)
        assert should_inject is False

    def test_format_specific_anomaly_types(self):
        """Test format-specific anomaly type selection."""
        # Test Apache format
        injector = AnomalyInjector(
            self.config, "apache_common", self.start_time, self.total_duration
        )
        relevant_types = injector.relevant_anomaly_types
        assert AnomalyType.FAILED_AUTH in relevant_types
        assert AnomalyType.BRUTE_FORCE in relevant_types

        # Test JSON format
        injector = AnomalyInjector(
            self.config, "json", self.start_time, self.total_duration
        )
        relevant_types = injector.relevant_anomaly_types
        assert AnomalyType.HIGH_LATENCY in relevant_types
        assert AnomalyType.MEMORY_SPIKE in relevant_types

    @patch('random.Random.random')
    def test_anomaly_injection_probability(self, mock_random):
        """Test anomaly injection based on probability."""
        injector = AnomalyInjector(
            self.config, "json", self.start_time, self.total_duration
        )

        timestamp = self.start_time + timedelta(minutes=30)

        # Should inject when random < base_rate
        mock_random.return_value = 0.05  # Less than base_rate (0.1)
        should_inject = injector.should_inject_anomaly(timestamp)
        assert should_inject is True

        # Should not inject when random >= base_rate
        mock_random.return_value = 0.15  # Greater than base_rate (0.1)
        should_inject = injector.should_inject_anomaly(timestamp)
        assert should_inject is False

    def test_generate_anomaly(self):
        """Test anomaly generation."""
        injector = AnomalyInjector(
            self.config, "json", self.start_time, self.total_duration
        )

        timestamp = self.start_time + timedelta(minutes=30)
        base_log_data = {"timestamp": timestamp, "level": "INFO", "message": "Test"}

        # Force high probability to ensure anomaly generation
        with patch.object(injector, 'should_inject_anomaly', return_value=True):
            anomaly = injector.generate_anomaly(timestamp, base_log_data)

        assert anomaly is not None
        assert isinstance(anomaly, AnomalyEvent)
        assert anomaly.timestamp == timestamp
        assert 0.0 <= anomaly.severity <= 1.0
        assert isinstance(anomaly.metadata, dict)

    def test_high_latency_anomaly_metadata(self):
        """Test high latency anomaly metadata generation."""
        injector = AnomalyInjector(
            self.config, "json", self.start_time, self.total_duration
        )

        metadata = injector._generate_anomaly_metadata(
            AnomalyType.HIGH_LATENCY, 0.5, {}
        )

        assert "response_time" in metadata
        assert "normal_response_time" in metadata
        assert "anomaly_multiplier" in metadata
        assert metadata["response_time"] > metadata["normal_response_time"]
        assert metadata["severity"] == 0.5

    def test_memory_spike_anomaly_metadata(self):
        """Test memory spike anomaly metadata generation."""
        injector = AnomalyInjector(
            self.config, "json", self.start_time, self.total_duration
        )

        metadata = injector._generate_anomaly_metadata(
            AnomalyType.MEMORY_SPIKE, 0.8, {}
        )

        assert "memory_usage" in metadata
        assert "normal_memory" in metadata
        assert "memory_threshold" in metadata
        assert metadata["memory_usage"] >= 80.0  # Should be in anomalous range
        assert metadata["memory_threshold"] == 80.0

    def test_failed_auth_anomaly_metadata(self):
        """Test failed authentication anomaly metadata generation."""
        injector = AnomalyInjector(
            self.config, "apache_common", self.start_time, self.total_duration
        )

        metadata = injector._generate_anomaly_metadata(AnomalyType.FAILED_AUTH, 0.7, {})

        assert "failed_attempts" in metadata
        assert "auth_method" in metadata
        assert "source_ip" in metadata
        assert "user_agent" in metadata
        assert metadata["failed_attempts"] >= 1

    def test_apply_apache_anomaly(self):
        """Test applying anomaly to Apache log format."""
        injector = AnomalyInjector(
            self.config, "apache_common", self.start_time, self.total_duration
        )

        log_data = {
            "ip": "192.168.1.1",
            "status_code": 200,
            "method": "GET",
            "url": "/index.html",
        }

        anomaly = AnomalyEvent(
            anomaly_type=AnomalyType.FAILED_AUTH,
            timestamp=self.start_time,
            severity=0.5,
            metadata={"source_ip": "10.0.0.1"},
        )

        modified_log = injector.apply_anomaly_to_log(log_data, anomaly)

        assert "anomaly" in modified_log
        assert modified_log["status_code"] == 401  # Failed auth
        assert modified_log["anomaly"]["type"] == "failed_auth"
        assert modified_log["anomaly"]["severity"] == 0.5

    def test_apply_json_anomaly(self):
        """Test applying anomaly to JSON log format."""
        injector = AnomalyInjector(
            self.config, "json", self.start_time, self.total_duration
        )

        log_data = {
            "timestamp": self.start_time,
            "level": "INFO",
            "message": "Processing request",
        }

        anomaly = AnomalyEvent(
            anomaly_type=AnomalyType.HIGH_LATENCY,
            timestamp=self.start_time,
            severity=0.8,
            metadata={"response_time": 5000},
        )

        modified_log = injector.apply_anomaly_to_log(log_data, anomaly)

        assert "anomaly" in modified_log
        assert modified_log["response_time"] == 5000
        assert modified_log["level"] == "WARNING"  # Escalated due to anomaly
        assert modified_log["anomaly"]["type"] == "high_latency"

    def test_correlation_handling(self):
        """Test anomaly correlation."""
        config = AnomalyConfig(
            enabled=True, seed=42, correlation_probability=1.0  # Force correlation
        )
        injector = AnomalyInjector(config, "json", self.start_time, self.total_duration)

        timestamp1 = self.start_time
        timestamp2 = self.start_time + timedelta(minutes=1)  # Within window

        # Generate first anomaly and add it to correlation
        correlation_id1 = injector._handle_correlation(
            AnomalyType.HIGH_LATENCY, timestamp1
        )
        assert correlation_id1 is not None

        # Create a dummy anomaly event and add it to correlation
        dummy_anomaly = AnomalyEvent(
            anomaly_type=AnomalyType.HIGH_LATENCY,
            timestamp=timestamp1,
            severity=0.5,
            metadata={},
            correlation_id=correlation_id1,
        )
        injector._add_to_correlation(correlation_id1, dummy_anomaly)

        # Second anomaly should get same correlation ID
        correlation_id2 = injector._handle_correlation(
            AnomalyType.MEMORY_SPIKE, timestamp2
        )
        assert correlation_id2 == correlation_id1

    def test_suspicious_ip_generation(self):
        """Test suspicious IP generation."""
        injector = AnomalyInjector(
            self.config, "apache_common", self.start_time, self.total_duration
        )

        suspicious_ip = injector._generate_suspicious_ip()

        assert isinstance(suspicious_ip, str)
        assert "." in suspicious_ip  # Should be IPv4 format

        # Generate multiple IPs to check variety
        ips = [injector._generate_suspicious_ip() for _ in range(10)]
        unique_ips = set(ips)
        assert len(unique_ips) > 1  # Should have variety

    def test_suspicious_user_agent_generation(self):
        """Test suspicious user agent generation."""
        injector = AnomalyInjector(
            self.config, "apache_common", self.start_time, self.total_duration
        )

        user_agent = injector._generate_suspicious_user_agent()

        assert isinstance(user_agent, str)
        assert len(user_agent) > 0

        # Should be one of the predefined suspicious agents
        suspicious_agents = [
            "curl/7.68.0",
            "wget/1.20.3",
            "python-requests/2.25.1",
            "sqlmap/1.4.9",
            "Nmap Scripting Engine",
        ]

        # Generate multiple to ensure we get variety
        agents = [injector._generate_suspicious_user_agent() for _ in range(20)]
        found_expected = any(agent in suspicious_agents for agent in agents)
        assert found_expected


class TestIntegrationWithPatterns:
    """Test anomaly injection with temporal patterns."""

    def test_burst_pattern_integration(self):
        """Test burst pattern integration."""
        pattern = AnomalyPatternConfig(
            pattern_type=TemporalPattern.BURST,
            anomaly_types=[AnomalyType.BRUTE_FORCE],
            base_rate=0.1,
            peak_rate=0.9,
            duration="10m",
        )

        config = AnomalyConfig(enabled=True, seed=42, patterns=[pattern])

        start_time = datetime(2023, 1, 1, 12, 0, 0)
        total_duration = timedelta(hours=1)

        injector = AnomalyInjector(config, "apache_common", start_time, total_duration)

        # During burst (should have high anomaly rate)
        burst_time = start_time + timedelta(minutes=5)

        # Test multiple times to verify high probability
        injection_count = 0
        test_runs = 100

        for _ in range(test_runs):
            if injector.should_inject_anomaly(burst_time):
                injection_count += 1

        # Should inject anomalies much more frequently during burst
        injection_rate = injection_count / test_runs
        assert injection_rate > 0.5  # Should be high during burst

        # Outside burst (should have lower anomaly rate)
        normal_time = start_time + timedelta(minutes=30)

        injection_count = 0
        for _ in range(test_runs):
            if injector.should_inject_anomaly(normal_time):
                injection_count += 1

        injection_rate = injection_count / test_runs
        assert injection_rate < 0.2  # Should be low outside burst

    def test_multiple_patterns(self):
        """Test multiple overlapping patterns."""
        pattern1 = AnomalyPatternConfig(
            pattern_type=TemporalPattern.CONSTANT,
            anomaly_types=[AnomalyType.FAILED_AUTH],
            base_rate=0.1,
        )

        pattern2 = AnomalyPatternConfig(
            pattern_type=TemporalPattern.BURST,
            anomaly_types=[AnomalyType.HIGH_LATENCY],
            base_rate=0.05,
            peak_rate=0.3,
            duration="15m",
            start_time="10m",
        )

        config = AnomalyConfig(enabled=True, seed=42, patterns=[pattern1, pattern2])

        start_time = datetime(2023, 1, 1, 12, 0, 0)
        total_duration = timedelta(hours=1)

        injector = AnomalyInjector(config, "json", start_time, total_duration)

        # Test at overlap time (pattern1 constant + pattern2 burst)
        overlap_time = start_time + timedelta(minutes=15)

        # Should use the maximum rate from active patterns
        injection_count = 0
        test_runs = 100

        for _ in range(test_runs):
            if injector.should_inject_anomaly(overlap_time):
                injection_count += 1

        injection_rate = injection_count / test_runs
        assert injection_rate > 0.15  # Should be higher due to burst pattern
