"""Data generators for realistic log content."""

import random
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from ipaddress import IPv4Address, IPv6Address

from faker import Faker


class DataGenerator:
    """Generate realistic log data."""
    
    def __init__(self, config):
        self.config = config
        self.fake = Faker()
        
        # Pre-generate common data for better performance
        self._pregenerate_data()
    
    def _pregenerate_data(self):
        """Pre-generate common data for better performance."""
        # Common IP addresses
        self.ip_addresses = [
            str(self.fake.ipv4_private()) for _ in range(1000)
        ]
        
        # Common user agents
        self.user_agents = [
            self.fake.user_agent() for _ in range(100)
        ]
        
        # Common URLs
        self.urls = [
            self.fake.uri_path() for _ in range(500)
        ]
        
        # Common hostnames
        self.hostnames = [
            self.fake.hostname() for _ in range(200)
        ]
        
        # Common usernames
        self.usernames = [
            self.fake.user_name() for _ in range(300)
        ]
        
        # HTTP status codes with realistic distribution
        self.http_status_codes = [
            200, 200, 200, 200, 200, 200, 200, 200,  # 200 OK - most common
            404, 404, 404,  # 404 Not Found
            500, 500,  # 500 Internal Server Error
            301, 302,  # Redirects
            403, 401,  # Forbidden, Unauthorized
            503, 502,  # Service Unavailable, Bad Gateway
        ]
        
        # Response sizes (bytes)
        self.response_sizes = [
            1024, 2048, 4096, 8192, 16384, 32768, 65536,
            1000, 1500, 3000, 5000, 10000, 25000, 50000,
        ]
        
        # Process names
        self.process_names = [
            "nginx", "apache2", "httpd", "sshd", "systemd", "kernel",
            "docker", "python", "java", "nodejs", "postgres", "mysql",
            "redis", "mongodb", "elasticsearch", "logstash", "kibana",
        ]
        
        # Common log messages by level
        self.message_templates = {
            "DEBUG": [
                "Debug: Processing request for user {user_id}",
                "Debug: Database query executed in {query_time}ms",
                "Debug: Cache hit for key {cache_key}",
                "Debug: Memory usage: {memory_usage}MB",
                "Debug: Processing {item_count} items",
                "Debug: API call to {api_endpoint}",
                "Debug: File {filename} processed successfully",
                "Debug: Connection established to {host}:{port}",
            ],
            "INFO": [
                "User {user_id} logged in successfully",
                "Request processed in {response_time}ms",
                "File {filename} uploaded successfully",
                "Database connection established",
                "Service started on port {port}",
                "Processing batch of {batch_size} items",
                "API endpoint {endpoint} called",
                "Configuration loaded from {config_file}",
                "Health check passed",
                "Session created for user {user_id}",
            ],
            "WARNING": [
                "High memory usage detected: {memory_percent}%",
                "Slow database query: {query_time}ms",
                "Connection timeout for {host}",
                "Rate limit exceeded for IP {ip_address}",
                "Disk space low: {disk_usage}% full",
                "Authentication failed for user {username}",
                "Deprecated API endpoint {endpoint} used",
                "Cache miss for key {cache_key}",
                "Service degraded performance",
                "Invalid input received: {error_details}",
            ],
            "ERROR": [
                "Failed to connect to database: {error_message}",
                "File not found: {filename}",
                "Permission denied for user {username}",
                "Invalid API key provided",
                "Service unavailable: {service_name}",
                "Processing failed for item {item_id}",
                "Connection lost to {host}:{port}",
                "Authentication service error",
                "File upload failed: {error_details}",
                "Database query failed: {query_error}",
            ],
            "CRITICAL": [
                "System out of memory",
                "Database connection pool exhausted",
                "Service completely unavailable",
                "Security breach detected",
                "Critical service failure: {service_name}",
                "Disk full - unable to write logs",
                "System overload - rejecting requests",
                "Authentication system failure",
                "Data corruption detected",
                "Emergency shutdown initiated",
            ],
        }
    
    def generate_message(self, level: str) -> str:
        """Generate a realistic log message for the given level."""
        templates = self.message_templates.get(level, self.message_templates["INFO"])
        template = random.choice(templates)
        
        # Fill in template variables
        variables = {
            "user_id": random.choice(self.usernames),
            "username": random.choice(self.usernames),
            "query_time": random.randint(10, 5000),
            "response_time": random.randint(5, 2000),
            "memory_usage": random.randint(100, 2000),
            "memory_percent": random.randint(50, 95),
            "cache_key": f"key_{random.randint(1000, 9999)}",
            "item_count": random.randint(1, 1000),
            "batch_size": random.randint(10, 500),
            "api_endpoint": f"/api/v1/{random.choice(['users', 'products', 'orders'])}",
            "endpoint": f"/api/{random.choice(['users', 'products', 'orders', 'auth'])}",
            "filename": f"{random.choice(['data', 'config', 'log'])}.{random.choice(['txt', 'json', 'xml'])}",
            "host": random.choice(self.hostnames),
            "port": random.choice([80, 443, 8080, 3000, 5432, 3306]),
            "ip_address": random.choice(self.ip_addresses),
            "service_name": random.choice(self.process_names),
            "item_id": f"item_{random.randint(1000, 9999)}",
            "config_file": f"config.{random.choice(['json', 'yaml', 'ini'])}",
            "disk_usage": random.randint(80, 99),
            "error_message": random.choice([
                "Connection refused", "Timeout", "Invalid credentials",
                "Permission denied", "Resource not found"
            ]),
            "error_details": random.choice([
                "Invalid format", "Missing required field", "Value out of range",
                "Malformed request", "Unsupported operation"
            ]),
            "query_error": random.choice([
                "Syntax error", "Table not found", "Column not found",
                "Constraint violation", "Connection timeout"
            ]),
        }
        
        try:
            return template.format(**variables)
        except KeyError:
            # If template has variables we don't have, return as-is
            return template
    
    def generate_web_log_fields(self) -> Dict[str, Any]:
        """Generate fields for web server logs (Apache/Nginx)."""
        return {
            "host": random.choice(self.ip_addresses),
            "remote_addr": random.choice(self.ip_addresses),
            "ident": "-",
            "authuser": random.choice(["-"] + self.usernames[:10]),
            "remote_user": random.choice(["-"] + self.usernames[:10]),
            "request": f"{random.choice(['GET', 'POST', 'PUT', 'DELETE'])} {random.choice(self.urls)} HTTP/1.1",
            "status": random.choice(self.http_status_codes),
            "size": random.choice(self.response_sizes),
            "body_bytes_sent": random.choice(self.response_sizes),
            "referer": random.choice(["-", self.fake.uri()]),
            "http_referer": random.choice(["-", self.fake.uri()]),
            "user_agent": random.choice(self.user_agents),
            "http_user_agent": random.choice(self.user_agents),
            "response_time": random.randint(1, 5000),
            "upstream_response_time": random.randint(1, 1000),
        }
    
    def generate_syslog_fields(self) -> Dict[str, Any]:
        """Generate fields for syslog entries."""
        return {
            "hostname": random.choice(self.hostnames),
            "process": random.choice(self.process_names),
            "pid": random.randint(1000, 9999),
            "facility": random.choice([0, 1, 2, 3, 4, 5, 6, 7, 16, 17, 18, 19, 20, 21, 22, 23]),
        }
    
    def generate_additional_fields(self) -> Dict[str, Any]:
        """Generate additional fields for enriched logging."""
        fields = {}
        
        # Add some fields randomly
        if random.random() < 0.3:  # 30% chance
            fields["thread_id"] = random.randint(1, 32)
        
        if random.random() < 0.2:  # 20% chance
            fields["session_id"] = self.fake.uuid4()
        
        if random.random() < 0.4:  # 40% chance
            fields["duration"] = random.randint(1, 1000)
        
        if random.random() < 0.1:  # 10% chance
            fields["error_code"] = random.choice([
                "ERR001", "ERR002", "ERR003", "WARN001", "WARN002"
            ])
        
        if random.random() < 0.3:  # 30% chance
            fields["component"] = random.choice([
                "auth", "db", "cache", "api", "worker", "scheduler"
            ])
        
        if random.random() < 0.2:  # 20% chance
            fields["request_id"] = self.fake.uuid4()
        
        if random.random() < 0.1:  # 10% chance
            fields["trace_id"] = self.fake.uuid4()
        
        return fields
    
    def generate_anomaly_fields(self) -> Dict[str, Any]:
        """Generate fields that might represent anomalies."""
        anomaly_fields = {}
        
        # High values that might indicate problems
        if random.random() < 0.05:  # 5% chance for anomalies
            anomaly_type = random.choice([
                "high_response_time", "high_memory", "high_cpu", 
                "unusual_ip", "high_error_rate"
            ])
            
            if anomaly_type == "high_response_time":
                anomaly_fields["response_time"] = random.randint(5000, 30000)
            elif anomaly_type == "high_memory":
                anomaly_fields["memory_usage"] = random.randint(90, 99)
            elif anomaly_type == "high_cpu":
                anomaly_fields["cpu_usage"] = random.randint(90, 100)
            elif anomaly_type == "unusual_ip":
                # Generate unusual IP patterns
                anomaly_fields["source_ip"] = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
            elif anomaly_type == "high_error_rate":
                anomaly_fields["error_count"] = random.randint(50, 200)
        
        return anomaly_fields
    
    def generate_structured_data(self) -> Dict[str, Any]:
        """Generate structured data for JSON-like formats."""
        return {
            "service": {
                "name": random.choice(self.process_names),
                "version": f"{random.randint(1, 5)}.{random.randint(0, 10)}.{random.randint(0, 10)}",
                "environment": random.choice(["development", "staging", "production"]),
            },
            "request": {
                "method": random.choice(["GET", "POST", "PUT", "DELETE", "PATCH"]),
                "url": random.choice(self.urls),
                "headers": {
                    "content-type": random.choice([
                        "application/json", "text/html", "application/xml",
                        "text/plain", "multipart/form-data"
                    ]),
                    "user-agent": random.choice(self.user_agents),
                },
                "body_size": random.choice(self.response_sizes),
            },
            "response": {
                "status": random.choice(self.http_status_codes),
                "size": random.choice(self.response_sizes),
                "duration": random.randint(1, 2000),
            },
            "user": {
                "id": random.randint(1000, 9999),
                "name": random.choice(self.usernames),
                "ip": random.choice(self.ip_addresses),
                "session_id": self.fake.uuid4(),
            },
            "system": {
                "hostname": random.choice(self.hostnames),
                "pid": random.randint(1000, 9999),
                "thread": random.randint(1, 32),
                "memory_usage": random.randint(100, 2000),
                "cpu_usage": random.randint(1, 100),
            },
        }