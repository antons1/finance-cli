"""Simple table formatter for CLI output."""


def format_table(
    rows: list[dict],
    columns: list[str] | None = None,
    headers: dict[str, str] | None = None,
) -> str:
    """Format a list of dicts as an aligned table.

    Args:
        rows: List of dicts with uniform keys.
        columns: Which keys to include (default: all keys from first row).
        headers: Map of key -> display label (default: use key as-is).
    """
    if not rows:
        return ""

    headers = headers or {}
    columns = columns or list(rows[0].keys())

    labels = [headers.get(c, c) for c in columns]

    def fmt(val):
        if val is None:
            return ""
        if isinstance(val, float):
            return f"{val:.2f}"
        return str(val)

    def is_numeric(col):
        return all(isinstance(r.get(col), (int, float)) or r.get(col) is None for r in rows)

    str_rows = [[fmt(r.get(c)) for c in columns] for r in rows]

    col_widths = [
        max(len(labels[i]), *(len(row[i]) for row in str_rows))
        for i in range(len(columns))
    ]

    numeric = [is_numeric(c) for c in columns]
    sep = "  "

    def align(val, width, right):
        return val.rjust(width) if right else val.ljust(width)

    header_line = sep.join(align(labels[i], col_widths[i], numeric[i]) for i in range(len(columns)))
    separator = sep.join("-" * col_widths[i] for i in range(len(columns)))

    data_lines = [
        sep.join(align(row[i], col_widths[i], numeric[i]) for i in range(len(columns)))
        for row in str_rows
    ]

    return "\n".join([header_line, separator] + data_lines) + "\n"
