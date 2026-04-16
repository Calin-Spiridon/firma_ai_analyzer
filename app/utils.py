def calculate_cagr(start, end, years):
    if start is None or end is None or start == 0:
        return None
    return (end / start) ** (1 / years) - 1