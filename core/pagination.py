from __future__ import annotations

from typing import Any, cast

from rest_framework.pagination import LimitOffsetPagination  # type: ignore[import-untyped]
from rest_framework.response import Response  # type: ignore[import-untyped]


class LimitOnlyPagination(LimitOffsetPagination):
    limit_query_param = "page_size"
    offset_query_param = None
    max_limit = 200

    def get_paginated_response(self, data: list[Any]) -> Response:
        return Response({
            "count": cast(int, self.count),  # type: ignore[reportUnknownMemberType]
            "page_size": cast(int, self.limit),  # type: ignore[reportUnknownMemberType]
            "results": data,
        })
