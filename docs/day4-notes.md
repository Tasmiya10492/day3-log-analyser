# Day 4 — API Client Notes

## 1. Support-Desk Worker Journey Map

### Goal
Help a support-desk worker retrieve reliable records from an API without needing to understand the technical details of HTTP requests.

### Journey

1. **Start:** The worker opens the support application and requests records.
2. **Request:** The application sends a GET request through the API client.
3. **Connection:** The client applies a timeout to avoid waiting indefinitely.
4. **Retry:** If the server returns HTTP 429 or 5xx, the client retries using exponential backoff and jitter. It respects the Retry-After header when available.
5. **Pagination:** The client retrieves records page by page until there are no more pages.
6. **Validation:** Pydantic validates the returned records before the application uses them.
7. **Result:** Valid records are returned to the application.
8. **Error handling:** If the request continues to fail or the response is invalid, an error is raised instead of silently accepting bad data.

### Worker outcome
The worker receives validated records or a clear error, rather than having to manage HTTP requests, retries, pagination, and validation manually.

## 2. SDK vs Direct REST

| SDK | Direct REST |
|---|---|
| Uses a library provided for an API or service. | Sends HTTP requests directly to API endpoints. |
| Often provides ready-made methods and data models. | The developer manages URLs, headers, parameters, and responses. |
| Can reduce the amount of code required. | Gives more control over request and response handling. |
| Depends on the SDK's supported features and updates. | Depends on the API documentation and HTTP client. |

### What this project uses

This project uses direct REST requests through the Python `httpx` library.

The API client handles GET requests, timeouts, retries, pagination, and response validation. Pydantic models validate the returned book records.

### Conclusion

An SDK is useful when a suitable and maintained SDK is available. Direct REST is useful when more control over HTTP behaviour is required or an SDK does not provide the required functionality.
