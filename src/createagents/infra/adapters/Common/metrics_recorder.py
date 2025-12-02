import time
from typing import Any, List, Optional

from ....domain.interfaces import IMetricsRecorder, LoggerInterface
from ...config import ChatMetrics


class MetricsRecorder(IMetricsRecorder):
    """Base class for recording metrics in handlers.

    This class provides common functionality for recording success and error metrics
    across different handler implementations (OpenAI, Ollama, etc.), eliminating
    code duplication and ensuring consistent metric collection.

    Implements IMetricsRecorder interface for dependency injection.

    Supports two recording modes:
    1. Response-based: Extracts tokens from API response objects
    2. Value-based: Accepts pre-calculated values (useful for streaming)
    """

    def __init__(
        self,
        logger: LoggerInterface,
        metrics_list: Optional[List[ChatMetrics]] = None,
    ):
        """Initialize the metrics recorder.

        Args:
            logger: Logger instance for logging operations.
            metrics_list: Optional list to store metrics. If None, creates a new list.
        """
        self._metrics = metrics_list if metrics_list is not None else []
        self._logger = logger

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
            provider_type: Type of provider ('openai' or 'ollama') for specific handling.
        """
        self.record_success_metrics(model, start_time, response, provider_type)

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
        metrics = ChatMetrics(
            model=model,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            success=True,
        )
        self._metrics.append(metrics)
        self._logger.info('Chat completed: %s', metrics)

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
            error: The error that occurred (can be string or Exception).
        """
        self.record_error_metrics(model, start_time, error)

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
        metrics = ChatMetrics(
            model=model,
            latency_ms=latency_ms,
            success=False,
            error_message=error_message,
        )
        self._metrics.append(metrics)
        self._logger.error('Chat failed: %s', metrics)

    def record_success_metrics(
        self,
        model: str,
        start_time: float,
        response_api: Any,
        provider_type: str = 'generic',
    ) -> None:
        """Record metrics for a successful operation.

        Args:
            model: The model name used for the operation.
            start_time: The timestamp when the operation started.
            response_api: The response object from the API.
            provider_type: Type of provider ('openai' or 'ollama') for specific handling.
        """
        latency = (time.time() - start_time) * 1000

        # Extract tokens based on provider type
        if provider_type == 'openai':
            tokens_used, prompt_tokens, completion_tokens = (
                self._extract_openai_tokens(response_api)
            )
            load_duration_ms = None
            prompt_eval_duration_ms = None
            eval_duration_ms = None
        elif provider_type == 'ollama':
            tokens_used, prompt_tokens, completion_tokens = (
                self._extract_ollama_tokens(response_api)
            )
            load_duration_ms, prompt_eval_duration_ms, eval_duration_ms = (
                self._extract_ollama_durations(response_api)
            )
        else:
            tokens_used = prompt_tokens = completion_tokens = None
            load_duration_ms = prompt_eval_duration_ms = eval_duration_ms = (
                None
            )

        metrics = ChatMetrics(
            model=model,
            latency_ms=latency,
            tokens_used=tokens_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            load_duration_ms=load_duration_ms,
            prompt_eval_duration_ms=prompt_eval_duration_ms,
            eval_duration_ms=eval_duration_ms,
            success=True,
        )
        self._metrics.append(metrics)
        self._logger.info('Chat completed: %s', metrics)

    def record_error_metrics(
        self, model: str, start_time: float, error: Any
    ) -> None:
        """Record metrics for a failed operation.

        Args:
            model: The model name used for the operation.
            start_time: The timestamp when the operation started.
            error: The error that occurred (can be string or Exception).
        """
        latency = (time.time() - start_time) * 1000
        error_message = str(error) if error else 'Unknown error'

        metrics = ChatMetrics(
            model=model,
            latency_ms=latency,
            success=False,
            error_message=error_message,
        )
        self._metrics.append(metrics)

    def get_metrics(self) -> List[ChatMetrics]:
        """Return a copy of collected metrics.

        Returns:
            A copy of the metrics list.
        """
        return self._metrics.copy()

    @staticmethod
    def _extract_openai_tokens(response_api: Any) -> tuple:
        """Extract token information from OpenAI response.

        Args:
            response_api: OpenAI response object.

        Returns:
            Tuple of (tokens_used, prompt_tokens, completion_tokens).
        """
        usage = getattr(response_api, 'usage', None)
        if usage:
            tokens_used = getattr(usage, 'total_tokens', None)
            prompt_tokens = getattr(usage, 'prompt_tokens', None)
            completion_tokens = getattr(usage, 'completion_tokens', None)
        else:
            tokens_used = None
            prompt_tokens = None
            completion_tokens = None

        return tokens_used, prompt_tokens, completion_tokens

    @staticmethod
    def _extract_ollama_tokens(response_api: Any) -> tuple:
        """Extract token information from Ollama response.

        Args:
            response_api: Ollama response object.

        Returns:
            Tuple of (tokens_used, prompt_tokens, completion_tokens).
        """
        prompt_eval_count = response_api.get('prompt_eval_count', 0)
        eval_count = response_api.get('eval_count', 0)
        total_tokens = prompt_eval_count + eval_count

        return total_tokens, prompt_eval_count, eval_count

    @staticmethod
    def _extract_ollama_durations(response_api: Any) -> tuple:
        """Extract duration information from Ollama response.

        Args:
            response_api: Ollama response object.

        Returns:
            Tuple of (load_duration_ms, prompt_eval_duration_ms, eval_duration_ms).
        """
        load_duration = response_api.get('load_duration')
        load_duration_ms = (
            load_duration / 1_000_000 if load_duration is not None else None
        )

        prompt_eval_duration = response_api.get('prompt_eval_duration')
        prompt_eval_duration_ms = (
            prompt_eval_duration / 1_000_000
            if prompt_eval_duration is not None
            else None
        )

        eval_duration = response_api.get('eval_duration')
        eval_duration_ms = (
            eval_duration / 1_000_000 if eval_duration is not None else None
        )

        return load_duration_ms, prompt_eval_duration_ms, eval_duration_ms
