from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

class LimitOnlyPagination(LimitOffsetPagination):
    """
    A custom pagination class that only uses a limit (renamed to page_size)
    and removes the 'page' or 'offset' numbering for simple list control.
    """
    limit_query_param = 'page_size'
    offset_query_param = None  # Disables manual offset in the URL
    max_limit = 200

    def get_paginated_response(self, data):
        return Response({
            'count': self.count,
            'page_size': self.limit,
            'results': data
        })
