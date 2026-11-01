import httpx
import pytest
from pydantic import ValidationError

from apiclient.client import APIClient
from apiclient.exceptions import APIError
from apiclient.models import BookPage
from apiclient.pagination import iter_records


def test_retries_after_server_error():
    request_count = 0
    sleep_calls = []

    def handler(request):
        nonlocal request_count
        request_count += 1

        if request_count == 1:
            return httpx.Response(500, json={"error": "Server error"})

        return httpx.Response(200, json={"status": "success"})

    with APIClient(
        "https://example.com",
        max_retries=2,
        transport=httpx.MockTransport(handler),
        sleep=sleep_calls.append,
        jitter=lambda: 0,
    ) as api:
        result = api.get("/test")

    assert result == {"status": "success"}
    assert request_count == 2
    assert sleep_calls == [1.0]


def test_does_not_retry_client_error():
    request_count = 0
    sleep_calls = []

    def handler(request):
        nonlocal request_count
        request_count += 1
        return httpx.Response(400, json={"error": "Bad request"})

    with APIClient(
        "https://example.com",
        max_retries=3,
        transport=httpx.MockTransport(handler),
        sleep=sleep_calls.append,
        jitter=lambda: 0,
    ) as api:
        with pytest.raises(APIError) as error:
            api.get("/test")

    assert error.value.status_code == 400
    assert request_count == 1
    assert sleep_calls == []


def test_respects_retry_after_header():
    request_count = 0
    sleep_calls = []

    def handler(request):
        nonlocal request_count
        request_count += 1

        if request_count == 1:
            return httpx.Response(
                429,
                headers={"Retry-After": "2"},
                json={"error": "Too many requests"},
            )

        return httpx.Response(200, json={"status": "success"})

    with APIClient(
        "https://example.com",
        max_retries=2,
        transport=httpx.MockTransport(handler),
        sleep=sleep_calls.append,
        jitter=lambda: 0,
    ) as api:
        result = api.get("/test")

    assert result == {"status": "success"}
    assert request_count == 2
    assert sleep_calls == [2.0]


def test_retries_after_timeout():
    request_count = 0
    sleep_calls = []

    def handler(request):
        nonlocal request_count
        request_count += 1

        if request_count == 1:
            raise httpx.ReadTimeout("Request timed out")

        return httpx.Response(200, json={"status": "success"})

    with APIClient(
        "https://example.com",
        max_retries=2,
        transport=httpx.MockTransport(handler),
        sleep=sleep_calls.append,
        jitter=lambda: 0,
    ) as api:
        result = api.get("/test")

    assert result == {"status": "success"}
    assert request_count == 2
    assert sleep_calls == [1.0]


def test_rejects_invalid_book_data():
    invalid_response = {
        "items": [
            {
                "id": "not-a-number",
                "name": "Birch 0001",
                "status": "Available",
                "category": "Fiction",
                "created": "2026-10-29T10:30:00",
            }
        ],
        "page": 1,
        "page_size": 5,
        "total": 1,
        "has_more": False,
    }

    with pytest.raises(ValidationError):
        BookPage.model_validate(invalid_response)


def test_raises_error_after_all_retries_are_exhausted():
    request_count = 0
    sleep_calls = []

    def handler(request):
        nonlocal request_count
        request_count += 1
        return httpx.Response(500, json={"error": "Server error"})

    with APIClient(
        "https://example.com",
        max_retries=2,
        transport=httpx.MockTransport(handler),
        sleep=sleep_calls.append,
        jitter=lambda: 0,
    ) as api:
        with pytest.raises(APIError) as error:
            api.get("/test")

    assert error.value.status_code == 500
    assert request_count == 3
    assert sleep_calls == [1.0, 2.0]


def test_retries_after_network_error():
    request_count = 0
    sleep_calls = []

    def handler(request):
        nonlocal request_count
        request_count += 1

        if request_count == 1:
            raise httpx.ConnectError("Connection failed")

        return httpx.Response(200, json={"status": "success"})

    with APIClient(
        "https://example.com",
        max_retries=2,
        transport=httpx.MockTransport(handler),
        sleep=sleep_calls.append,
        jitter=lambda: 0,
    ) as api:
        result = api.get("/test")

    assert result == {"status": "success"}
    assert request_count == 2
    assert sleep_calls == [1.0]


def test_pagination_retrieves_all_records():
    def make_book(book_id, name):
        return {
            "id": book_id,
            "name": name,
            "status": "Available",
            "category": "Fiction",
            "created": "2026-10-29T10:30:00",
        }

    def handler(request):
        page = int(request.url.params["page"])

        if page == 1:
            return httpx.Response(
                200,
                json={
                    "items": [
                        make_book(1, "Birch 0001"),
                        make_book(2, "Dune 0002"),
                    ],
                    "page": 1,
                    "page_size": 2,
                    "total": 3,
                    "has_more": True,
                },
            )

        return httpx.Response(
            200,
            json={
                "items": [make_book(3, "Atlas 0003")],
                "page": 2,
                "page_size": 2,
                "total": 3,
                "has_more": False,
            },
        )

    with APIClient(
        "https://example.com",
        transport=httpx.MockTransport(handler),
    ) as api:
        books = list(iter_records(api, "/books", page_size=2))

    assert len(books) == 3
    assert [book.id for book in books] == [1, 2, 3]
    assert all(isinstance(book.created, object) for book in books)


def test_pagination_rejects_invalid_records():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "items": [
                    {
                        "id": "invalid",
                        "name": "Birch 0001",
                        "status": "Available",
                        "category": "Fiction",
                        "created": "2026-10-29T10:30:00",
                    }
                ],
                "page": 1,
                "page_size": 5,
                "total": 1,
                "has_more": False,
            },
        )

    with APIClient(
        "https://example.com",
        transport=httpx.MockTransport(handler),
    ) as api:
        with pytest.raises(ValidationError):
            list(iter_records(api, "/books", page_size=5))
