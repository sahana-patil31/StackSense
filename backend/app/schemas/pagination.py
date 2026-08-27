def paginate(query, page: int | None, page_size: int | None):
    if page is None and page_size is None:
        return query.all(), None
    page = page or 1
    page_size = min(page_size or 25, 100)
    total = query.count()
    return query.offset((page - 1) * page_size).limit(page_size).all(), {"page": page, "page_size": page_size, "total": total}