# platform/observability/otel.py
"""
OpenTelemetry Observability Module for Sophia AI Platform
Provides distributed tracing, metrics, and logging capabilities.
"""

import logging
import os
from typing import Any, Dict, Optional, Callable
from contextlib import contextmanager
from functools import wraps

try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.trace.propagation.tracecontext import TraceContextPropagator
    from opentelemetry.baggage.propagation import BaggagePropagator
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    # Define dummy classes/functions for when opentelemetry is not available
    class DummyTracer:
        def start_as_current_span(self, name): return DummySpan()
        def start_span(self, name): return DummySpan()

    class DummySpan:
        def set_attribute(self, key, value): pass
        def set_status(self, status): pass
        def record_exception(self, exception): pass
        def end(self): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass

    class DummyMeter:
        def create_counter(self, name, description=""): return DummyCounter()
        def create_histogram(self, name, description=""): return DummyHistogram()
        def create_gauge(self, name, description=""): return DummyGauge()

    class DummyCounter:
        def add(self, amount, attributes=None): pass

    class DummyHistogram:
        def record(self, amount, attributes=None): pass

    class DummyGauge:
        def set(self, amount, attributes=None): pass

    def trace(name): return lambda f: f
    def metrics(): return DummyMeter()

# Configure logging
logger = logging.getLogger(__name__)


class ObservabilityManager:
    """
    OpenTelemetry Observability Manager for Sophia AI Platform
    Provides tracing, metrics, and logging instrumentation
    """

    def __init__(
        self,
        service_name: str = "sophia-ai-platform",
        service_version: str = "1.0.0",
        otlp_endpoint: Optional[str] = None,
        enable_tracing: bool = True,
        enable_metrics: bool = True,
    ):
        """
        Initialize Observability Manager

        Args:
            service_name: Name of the service
            service_version: Version of the service
            otlp_endpoint: OTLP endpoint for exporting telemetry
            enable_tracing: Whether to enable distributed tracing
            enable_metrics: Whether to enable metrics collection
        """
        self.service_name = service_name
        self.service_version = service_version
        self.otlp_endpoint = otlp_endpoint or os.getenv("OTLP_ENDPOINT", "http://localhost:4317")
        self.enable_tracing = enable_tracing and OPENTELEMETRY_AVAILABLE
        self.enable_metrics = enable_metrics and OPENTELEMETRY_AVAILABLE

        if not OPENTELEMETRY_AVAILABLE:
            logger.warning("OpenTelemetry not available, using dummy implementation")

        self._setup_tracing()
        self._setup_metrics()

    def _setup_tracing(self):
        """Setup OpenTelemetry tracing"""
        if not self.enable_tracing:
            self.tracer = DummyTracer()
            return

        try:
            # Set up tracer provider
            trace.set_tracer_provider(TracerProvider())
            tracer_provider = trace.get_tracer_provider()

            # Configure OTLP exporter
            otlp_exporter = OTLPSpanExporter(
                endpoint=self.otlp_endpoint,
                insecure=True,
            )

            # Add span processor
            span_processor = BatchSpanProcessor(otlp_exporter)
            tracer_provider.add_span_processor(span_processor)

            # Set up propagators
            from opentelemetry.propagators.composite import CompositePropagator
            trace.set_global_textmap_propagator(
                CompositePropagator([TraceContextPropagator(), BaggagePropagator()])
            )

            # Get tracer
            self.tracer = trace.get_tracer(
                self.service_name,
                self.service_version,
            )

            logger.info(f"✅ OpenTelemetry tracing configured for {self.service_name}")

        except Exception as e:
            logger.error(f"❌ Failed to setup tracing: {e}")
            self.tracer = DummyTracer()

    def _setup_metrics(self):
        """Setup OpenTelemetry metrics"""
        if not self.enable_metrics:
            self.meter = DummyMeter()
            return

        try:
            # Configure OTLP metric exporter
            otlp_metric_exporter = OTLPMetricExporter(
                endpoint=self.otlp_endpoint,
                insecure=True,
            )

            # Set up metric reader
            metric_reader = PeriodicExportingMetricReader(
                otlp_metric_exporter,
                export_interval_millis=60000,  # Export every 60 seconds
            )

            # Set up meter provider
            metrics.set_meter_provider(MeterProvider(metric_readers=[metric_reader]))
            meter_provider = metrics.get_meter_provider()

            # Get meter
            self.meter = meter_provider.get_meter(
                self.service_name,
                self.service_version,
            )

            # Create common metrics
            self.request_counter = self.meter.create_counter(
                "http_requests_total",
                description="Total number of HTTP requests"
            )
            self.request_duration = self.meter.create_histogram(
                "http_request_duration_seconds",
                description="HTTP request duration in seconds"
            )
            self.error_counter = self.meter.create_counter(
                "errors_total",
                description="Total number of errors"
            )

            logger.info(f"✅ OpenTelemetry metrics configured for {self.service_name}")

        except Exception as e:
            logger.error(f"❌ Failed to setup metrics: {e}")
            self.meter = DummyMeter()

    def instrument_fastapi(self, app):
        """Instrument FastAPI application"""
        if not self.enable_tracing or not OPENTELEMETRY_AVAILABLE:
            return

        try:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("✅ FastAPI instrumentation enabled")
        except Exception as e:
            logger.error(f"❌ Failed to instrument FastAPI: {e}")

    @contextmanager
    def trace_span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Context manager for creating spans

        Args:
            name: Span name
            attributes: Span attributes
        """
        with self.tracer.start_as_current_span(name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            try:
                yield span
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    def trace_function(
        self,
        name: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Decorator for tracing functions

        Args:
            name: Custom span name (defaults to function name)
            attributes: Additional span attributes
        """
        def decorator(func: Callable):
            span_name = name or f"{func.__module__}.{func.__qualname__}"

            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.trace_span(span_name, attributes) as span:
                    # Add function arguments as span attributes (be careful with sensitive data)
                    if attributes is None:
                        span.set_attribute("function.args_count", len(args))
                        span.set_attribute("function.kwargs_count", len(kwargs))

                    try:
                        result = func(*args, **kwargs)
                        span.set_attribute("function.success", True)
                        return result
                    except Exception as e:
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.set_attribute("function.success", False)
                        raise

            return wrapper
        return decorator

    def record_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Record HTTP request metrics"""
        if not self.enable_metrics:
            return

        # Prepare attributes
        attrs = {
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
        }
        if attributes:
            attrs.update(attributes)

        # Record metrics
        self.request_counter.add(1, attrs)
        self.request_duration.record(duration, attrs)

        if status_code >= 400:
            self.error_counter.add(1, {
                **attrs,
                "error_type": "http_error"
            })

    def record_error(
        self,
        error_type: str,
        error_message: str,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Record error metrics"""
        if not self.enable_metrics:
            return

        attrs = {
            "error_type": error_type,
            "error_message": error_message[:100],  # Truncate long messages
        }
        if attributes:
            attrs.update(attributes)

        self.error_counter.add(1, attrs)


# Global observability manager instance
_observability_manager = None


def get_observability_manager() -> ObservabilityManager:
    """Get global observability manager instance"""
    global _observability_manager
    if _observability_manager is None:
        _observability_manager = ObservabilityManager()
    return _observability_manager


def init_observability(
    service_name: str = "sophia-ai-platform",
    service_version: str = "1.0.0",
    otlp_endpoint: Optional[str] = None,
) -> ObservabilityManager:
    """
    Initialize global observability

    Args:
        service_name: Name of the service
        service_version: Version of the service
        otlp_endpoint: OTLP endpoint for exporting telemetry

    Returns:
        ObservabilityManager instance
    """
    global _observability_manager
    _observability_manager = ObservabilityManager(
        service_name=service_name,
        service_version=service_version,
        otlp_endpoint=otlp_endpoint,
    )
    return _observability_manager


def trace_function(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None
):
    """
    Convenience decorator for tracing functions

    Args:
        name: Custom span name
        attributes: Additional span attributes
    """
    return get_observability_manager().trace_function(name, attributes)


def trace_span(name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Convenience context manager for creating spans

    Args:
        name: Span name
        attributes: Span attributes
    """
    return get_observability_manager().trace_span(name, attributes)


def record_request(
    method: str,
    endpoint: str,
    status_code: int,
    duration: float,
    attributes: Optional[Dict[str, Any]] = None
):
    """Convenience function to record HTTP request metrics"""
    get_observability_manager().record_request(method, endpoint, status_code, duration, attributes)


def record_error(
    error_type: str,
    error_message: str,
    attributes: Optional[Dict[str, Any]] = None
):
    """Convenience function to record error metrics"""
    get_observability_manager().record_error(error_type, error_message, attributes)


# FastAPI middleware for automatic request tracing and metrics
def get_observability_middleware():
    """Get FastAPI middleware for observability"""
    from fastapi import Request, Response
    import time

    async def observability_middleware(request: Request, call_next):
        start_time = time.time()

        with trace_span(
            f"http_{request.method.lower()}",
            {
                "http.method": request.method,
                "http.url": str(request.url),
                "http.scheme": request.url.scheme,
                "http.host": request.url.host,
                "http.path": request.url.path,
            }
        ):
            try:
                response = await call_next(request)
                duration = time.time() - start_time

                # Record metrics
                record_request(
                    method=request.method,
                    endpoint=request.url.path,
                    status_code=response.status_code,
                    duration=duration,
                )

                return response

            except Exception as e:
                duration = time.time() - start_time

                # Record error metrics
                record_error(
                    error_type="http_exception",
                    error_message=str(e),
                    attributes={
                        "http.method": request.method,
                        "http.path": request.url.path,
                    }
                )

                # Record failed request
                record_request(
                    method=request.method,
                    endpoint=request.url.path,
                    status_code=500,
                    duration=duration,
                    attributes={"error": True}
                )

                raise

    return observability_middleware