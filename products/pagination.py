from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination, CursorPagination
from rest_framework.response import Response

class CustomProductPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'meta': {
                'total_products': self.page.paginator.count,
                'current_page': self.page.number,
                'total_pages': self.page.paginator.num_pages,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
            },
            'products': data
        })


class RelatedLimitOffset(LimitOffsetPagination):
    default_limit = 4
    max_limit = 24


class ReviewCursorPagination(CursorPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50
    ordering = ("-created_at", "-id")
