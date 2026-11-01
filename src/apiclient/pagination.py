from collections.abc import Iterator

from apiclient.client import APIClient
from apiclient.models import BookPage


def iter_records(
    api: APIClient,
    endpoint: str,
    page_size: int = 5,
) -> Iterator:
    """Retrieve validated records from a page-based API."""

    page = 1

    while True:
        response = api.get(
            endpoint,
            params={
                "page": page,
                "page_size": page_size,
            },
        )

        validated_page = BookPage.model_validate(response)

        yield from validated_page.items

        if not validated_page.has_more:
            break

        page += 1
