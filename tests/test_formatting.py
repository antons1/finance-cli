"""Tests for table formatting — written before implementation."""

import pytest

from finance.formatting import format_table


class TestFormatTable:
    def test_simple_table(self):
        rows = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]
        result = format_table(rows)
        lines = result.strip().split("\n")
        assert len(lines) == 4  # header + separator + 2 rows
        assert "name" in lines[0].lower() or "Name" in lines[0]
        assert "Alice" in lines[2]
        assert "Bob" in lines[3]

    def test_columns_are_aligned(self):
        rows = [
            {"short": "a", "longer_value": "hello"},
            {"short": "bb", "longer_value": "hi"},
        ]
        result = format_table(rows)
        lines = result.strip().split("\n")
        # Second column ("longer_value") should start at same position in header and data
        header_pos = lines[0].index("longer_value")
        assert lines[2].index("hello") == header_pos
        assert lines[3].index("hi") == header_pos

    def test_empty_rows_returns_empty(self):
        result = format_table([])
        assert result == ""

    def test_numeric_values_right_aligned(self):
        rows = [
            {"name": "Konto", "balance": 15000.50},
            {"name": "Spare", "balance": 250000.00},
        ]
        result = format_table(rows)
        lines = result.strip().split("\n")
        # The shorter number should have leading spaces (right-aligned)
        assert "15000.50" in lines[2]
        assert "250000.00" in lines[3]
        # Right-aligned: 15000.50 should end at same column as 250000.00
        assert lines[2].index("0.50") == lines[3].index("0.00")

    def test_none_values_shown_as_empty(self):
        rows = [
            {"name": "Test", "value": None},
        ]
        result = format_table(rows)
        assert "None" not in result

    def test_custom_columns(self):
        rows = [
            {"a": 1, "b": 2, "c": 3},
        ]
        result = format_table(rows, columns=["a", "c"])
        assert "b" not in result.split("\n")[0]
        assert "a" in result.split("\n")[0]
        assert "c" in result.split("\n")[0]

    def test_header_labels(self):
        rows = [
            {"accountNumber": "123", "balance": 100},
        ]
        result = format_table(rows, headers={"accountNumber": "Account", "balance": "Balance"})
        assert "Account" in result.split("\n")[0]
        assert "accountNumber" not in result.split("\n")[0]

    def test_separator_line(self):
        rows = [{"a": 1}]
        result = format_table(rows)
        lines = result.strip().split("\n")
        assert all(c in "- " for c in lines[1].strip())
