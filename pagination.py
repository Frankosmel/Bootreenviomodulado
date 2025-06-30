def paginate_list(items, page: int, per_page: int = 3):
    start = page * per_page
    end = start + per_page
    return items[start:end], (len(items) > end)
