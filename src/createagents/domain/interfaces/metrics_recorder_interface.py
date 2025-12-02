from abc import ABC, abstractmethod
from typing import Any, List, Optional


class IMetricsRecorder(ABC):
    """Abstract interface for metrics recording.

    This interface allows handlers to record metrics without coupling
    to specific infrastructure implementations.

    There are two ways to record metrics:
    1. Using response object (useful when you have the API response):
       - record_success(model, start_time, response, provider_type)
       - record_error(model, start_time, error)

    2. Using pre-calculated values (useful for streaming):
       - record_success_with_values(model, latency_ms, tokens_used, ...)
       - record_error_with_values(model, latency_ms, error_message)
    """

    @abstractmethod
    def record_success(
        self,
        model: str,
        start_time: float,
        response: Any,
        provider_type: str = 'generic',
    ) -> None:
        """Record metrics for a successful operation using response object.

        Args:
            model: The model name used for the operation.
            start_time: The timestamp when the operation started.
            response: The response object from the API.
            provider_type: Type of provider for specific handling.
        """
        pass

    @abstractmethod
    def record_success_with_values(
        self,
        model: str,
        latency_ms: float,
        tokens_used: Optional[int] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
    ) -> None:
        """Record metrics for a successful operation using pre-calculated values.

        Useful for streaming where tokens are accumulated across iterations.

        Args:
            model: The model name used for the operation.
            latency_ms: The latency in milliseconds.
            tokens_used: Total tokens used.
            prompt_tokens: Prompt tokens used.
            completion_tokens: Completion tokens used.
        """
        pass

    @abstractmethod
    def record_error(
        self,
        model: str,
        start_time: float,
        error: Any,
    ) -> None:
        """Record metrics for a failed operation.

        Args:
            model: The model name used for the operation.
            start_time: The timestamp when the operation started.
            error: The error that occurred.
        """
        pass

    @abstractmethod
    def record_error_with_values(
        self,
        model: str,
        latency_ms: float,
        error_message: str,
    ) -> None:
        """Record metrics for a failed operation using pre-calculated values.

        Args:
            model: The model name used for the operation.
            latency_ms: The latency in milliseconds.
            error_message: The error message.
        """
        pass

    @abstractmethod
    def get_metrics(self) -> List[Any]:
        """Return collected metrics.

        Returns:
            List of collected metrics.
        """
        pass


__all__ = ['IMetricsRecorder']
