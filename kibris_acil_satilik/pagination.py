# core/pagination.py

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict


class CustomPagination(PageNumberPagination):
    """
    Custom pagination class that matches the frontend pagination display.
    Provides page numbers, first/next/previous/last page links.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'

    def get_paginated_response(self, data):
        # Calculate page numbers to display
        current_page = self.page.number
        total_pages = self.page.paginator.num_pages

        # Generate page numbers for pagination display (like "First 1 2 3 Next")
        page_numbers = []
        if total_pages <= 5:
            # If 5 or fewer pages, show all page numbers
            page_numbers = list(range(1, total_pages + 1))
        else:
            # Always include first, last, and current page
            if current_page <= 3:
                # Near the beginning: show first 5 pages
                page_numbers = list(range(1, 6))
            elif current_page >= total_pages - 2:
                # Near the end: show last 5 pages
                page_numbers = list(range(total_pages - 4, total_pages + 1))
            else:
                # In the middle: show current page, 2 before and 2 after
                page_numbers = list(range(current_page - 2, current_page + 3))

        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', total_pages),
            ('current_page', current_page),
            ('page_numbers', page_numbers),
            ('has_next', self.page.has_next()),
            ('has_previous', self.page.has_previous()),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('first_page', self.request.build_absolute_uri().split('?')[0] + '?page=1'),
            ('last_page', self.request.build_absolute_uri().split('?')[0] + f'?page={total_pages}'),
            ('results', data)
        ]))