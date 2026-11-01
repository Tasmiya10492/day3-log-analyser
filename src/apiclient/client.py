import random
import time
from collections.abc import Callable

import httpx

from apiclient.exceptions import APIError


class APIClient:
    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
        jitter: Callable[[], float] = random.random,
        transport: httpx.BaseTransport | None = None,
    ):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.sleep = sleep
        self.jitter = jitter

        self.client = httpx.Client(
            base_url=base_url,
            timeout=httpx.Timeout(timeout),
            transport=transport,
        )

    def get(self, endpoint: str, params: dict | None = None) -> dict:
        """Send a GET request and return the JSON response."""

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.get(endpoint, params=params)

                should_retry = response.status_code == 429 or 500 <= response.status_code <= 599

                if should_retry:
                    if attempt == self.max_retries:
                        raise APIError(
                            "API request failed after all retry attempts",
                            response.status_code,
                        )

                    retry_after = response.headers.get("Retry-After")

                    if retry_after is not None:
                        try:
                            delay = max(0.0, float(retry_after))
                        except ValueError:
                            delay = self._backoff_delay(attempt)
                    else:
                        delay = self._backoff_delay(attempt)

                    self.sleep(delay)
                    continue

                response.raise_for_status()
                return response.json()

            except (httpx.TimeoutException, httpx.NetworkError) as error:
                if attempt == self.max_retries:
                    raise APIError("API request failed after all retry attempts") from error

                self.sleep(self._backoff_delay(attempt))

            except httpx.HTTPStatusError as error:
                raise APIError(
                    f"API returned HTTP {error.response.status_code}",
                    error.response.status_code,
                ) from error

        raise APIError("API request failed")

    def _backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff with jitter."""

        return self.backoff_factor * (2**attempt) + self.jitter()

    def close(self) -> None:
        """Close the HTTP connection."""

        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
