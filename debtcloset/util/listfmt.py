"""Utilities for working with lists."""

import textwrap

DOUBLE_QUOTE = '"'
SPACE = " "


def align(
    strings: list[str],
    *,
    quote: str | None = DOUBLE_QUOTE,
    sep: str = ",",
    vertical: bool = True,
    trailsep: bool = True,
    indent: int = 4,
) -> str:
    """Concatenate strings with optional vertical alignment, quoting, and indentation.

    Args:
        strings: The strings to concatenate.
        quote: If provided, wrap each string in this character.
        sep: The separator to use between strings.
        vertical: Whether to concatenate the strings vertically (vs a single line, horizontally).
        trailsep: Whether to include a trailing separator.
        indent: The number of spaces to indent the output.
    """
    if quote:
        strings = [f'"{string}"' for string in strings]
    fullsep = f"{sep}\n" if vertical else sep
    expression = fullsep.join(strings)
    if trailsep:
        expression += sep
    if indent:
        expression = textwrap.indent(expression, SPACE * indent)
    return expression
