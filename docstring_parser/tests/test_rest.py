"""Tests for ReST-style docstring routines."""
import typing as T

import pytest

from docstring_parser.common import ParseError, RenderingStyle
from docstring_parser.rest import compose, parse


@pytest.mark.parametrize(
    "source, expected",
    [
        ("", None),
        ("\n", None),
        ("Short description", "Short description"),
        ("\nShort description\n", "Short description"),
        ("\n   Short description\n", "Short description"),
    ],
)
def test_short_description(source: str, expected: str) -> None:
    """Test parsing short description."""
    docstring = parse(source)
    assert docstring.short_description == expected
    assert docstring.description == expected
    assert docstring.long_description is None
    assert not docstring.meta


@pytest.mark.parametrize(
    "source, expected_short_desc, expected_long_desc, expected_blank",
    [
        (
            "Short description\n\nLong description",
            "Short description",
            "Long description",
            True,
        ),
        (
            """
            Short description

            Long description
            """,
            "Short description",
            "Long description",
            True,
        ),
        (
            """
            Short description

            Long description
            Second line
            """,
            "Short description",
            "Long description\nSecond line",
            True,
        ),
        (
            "Short description\nLong description",
            "Short description",
            "Long description",
            False,
        ),
        (
            """
            Short description
            Long description
            """,
            "Short description",
            "Long description",
            False,
        ),
        (
            "\nShort description\nLong description\n",
            "Short description",
            "Long description",
            False,
        ),
        (
            """
            Short description
            Long description
            Second line
            """,
            "Short description",
            "Long description\nSecond line",
            False,
        ),
    ],
)
def test_long_description(
    source: str,
    expected_short_desc: str,
    expected_long_desc: str,
    expected_blank: bool,
) -> None:
    """Test parsing long description."""
    docstring = parse(source)
    assert docstring.short_description == expected_short_desc
    assert docstring.long_description == expected_long_desc
    assert docstring.blank_after_short_description == expected_blank
    assert not docstring.meta


@pytest.mark.parametrize(
    "source, expected_short_desc, expected_long_desc, "
    "expected_blank_short_desc, expected_blank_long_desc, "
    "expected_full_desc",
    [
        (
            """
            Short description
            :meta: asd
            """,
            "Short description",
            None,
            False,
            False,
            "Short description",
        ),
        (
            """
            Short description
            Long description
            :meta: asd
            """,
            "Short description",
            "Long description",
            False,
            False,
            "Short description\nLong description",
        ),
        (
            """
            Short description
            First line
                Second line
            :meta: asd
            """,
            "Short description",
            "First line\n    Second line",
            False,
            False,
            "Short description\nFirst line\n    Second line",
        ),
        (
            """
            Short description

            First line
                Second line
            :meta: asd
            """,
            "Short description",
            "First line\n    Second line",
            True,
            False,
            "Short description\n\nFirst line\n    Second line",
        ),
        (
            """
            Short description

            First line
                Second line

            :meta: asd
            """,
            "Short description",
            "First line\n    Second line",
            True,
            True,
            "Short description\n\nFirst line\n    Second line",
        ),
        (
            """
            :meta: asd
            """,
            None,
            None,
            False,
            False,
            None,
        ),
    ],
)
def test_meta_newlines(
    source: str,
    expected_short_desc: T.Optional[str],
    expected_long_desc: T.Optional[str],
    expected_blank_short_desc: bool,
    expected_blank_long_desc: bool,
    expected_full_desc: T.Optional[str],
) -> None:
    """Test parsing newlines around description sections."""
    docstring = parse(source)
    assert docstring.short_description == expected_short_desc
    assert docstring.long_description == expected_long_desc
    assert docstring.blank_after_short_description == expected_blank_short_desc
    assert docstring.blank_after_long_description == expected_blank_long_desc
    assert docstring.description == expected_full_desc
    assert len(docstring.meta) == 1


def test_meta_with_multiline_description() -> None:
    """Test parsing multiline meta documentation."""
    docstring = parse(
        """
        Short description

        :meta: asd
            1
                2
            3
        """
    )
    assert docstring.short_description == "Short description"
    assert len(docstring.meta) == 1
    assert docstring.meta[0].args == ["meta"]
    assert docstring.meta[0].description == "asd\n1\n    2\n3"


def test_multiple_meta() -> None:
    """Test parsing multiple meta."""
    docstring = parse(
        """
        Short description

        :meta1: asd
            1
                2
            3
        :meta2: herp
        :meta3: derp
        """
    )
    assert docstring.short_description == "Short description"
    assert len(docstring.meta) == 3
    assert docstring.meta[0].args == ["meta1"]
    assert docstring.meta[0].description == "asd\n1\n    2\n3"
    assert docstring.meta[1].args == ["meta2"]
    assert docstring.meta[1].description == "herp"
    assert docstring.meta[2].args == ["meta3"]
    assert docstring.meta[2].description == "derp"


def test_meta_with_args() -> None:
    """Test parsing meta with additional arguments."""
    docstring = parse(
        """
        Short description

        :meta ene due rabe: asd
        """
    )
    assert docstring.short_description == "Short description"
    assert len(docstring.meta) == 1
    assert docstring.meta[0].args == ["meta", "ene", "due", "rabe"]
    assert docstring.meta[0].description == "asd"


def test_params() -> None:
    """Test parsing params."""
    docstring = parse("Short description")
    assert len(docstring.params) == 0

    docstring = parse(
        """
        Short description

        :param name: description 1
        :param int priority: description 2
        :param str? sender: description 3
        :param str? message: description 4, defaults to 'hello'
        :param str? multiline: long description 5,
        defaults to 'bye'
        """
    )
    assert len(docstring.params) == 5
    assert docstring.params[0].arg_name == "name"
    assert docstring.params[0].type_name is None
    assert docstring.params[0].description == "description 1"
    assert docstring.params[0].default is None
    assert not docstring.params[0].is_optional
    assert docstring.params[1].arg_name == "priority"
    assert docstring.params[1].type_name == "int"
    assert docstring.params[1].description == "description 2"
    assert not docstring.params[1].is_optional
    assert docstring.params[1].default is None
    assert docstring.params[2].arg_name == "sender"
    assert docstring.params[2].type_name == "str"
    assert docstring.params[2].description == "description 3"
    assert docstring.params[2].is_optional
    assert docstring.params[2].default is None
    assert docstring.params[3].arg_name == "message"
    assert docstring.params[3].type_name == "str"
    assert (
        docstring.params[3].description == "description 4, defaults to 'hello'"
    )
    assert docstring.params[3].is_optional
    assert docstring.params[3].default == "'hello'"
    assert docstring.params[4].arg_name == "multiline"
    assert docstring.params[4].type_name == "str"
    assert (
        docstring.params[4].description
        == "long description 5,\ndefaults to 'bye'"
    )
    assert docstring.params[4].is_optional
    assert docstring.params[4].default == "'bye'"

    docstring = parse(
        """
        Short description

        :param a: description a
        :type a: int
        :param int b: description b
        """
    )
    assert len(docstring.params) == 2
    assert docstring.params[0].arg_name == "a"
    assert docstring.params[0].type_name == "int"
    assert docstring.params[0].description == "description a"
    assert docstring.params[0].default is None
    assert not docstring.params[0].is_optional


def test_returns() -> None:
    """Test parsing returns."""
    docstring = parse(
        """
        Short description
        """
    )
    assert docstring.returns is None
    assert docstring.many_returns is not None
    assert len(docstring.many_returns) == 0

    docstring = parse(
        """
        Short description
        :returns: description
        """
    )
    assert docstring.returns is not None
    assert docstring.returns.type_name is None
    assert docstring.returns.description == "description"
    assert not docstring.returns.is_generator
    assert docstring.many_returns == [docstring.returns]

    docstring = parse(
        """
        Short description
        :returns int: description
        """
    )
    assert docstring.returns is not None
    assert docstring.returns.type_name == "int"
    assert docstring.returns.description == "description"
    assert not docstring.returns.is_generator
    assert docstring.many_returns == [docstring.returns]

    docstring = parse(
        """
        Short description
        :returns: description
        :rtype: int
        """
    )
    assert docstring.returns is not None
    assert docstring.returns.type_name == "int"
    assert docstring.returns.description == "description"
    assert not docstring.returns.is_generator
    assert docstring.many_returns == [docstring.returns]


def test_yields() -> None:
    """Test parsing yields."""
    docstring = parse(
        """
        Short description
        """
    )
    assert docstring.returns is None
    assert docstring.many_returns is not None
    assert len(docstring.many_returns) == 0

    docstring = parse(
        """
        Short description
        :yields: description
        """
    )
    assert docstring.returns is None
    assert docstring.yields is not None
    assert docstring.yields.type_name is None
    assert docstring.yields.description == "description"
    assert docstring.yields.is_generator
    assert docstring.many_returns is not None
    assert len(docstring.many_returns) == 0

    docstring = parse(
        """
        Short description
        :yields int: description
        """
    )
    assert docstring.returns is None
    assert docstring.yields is not None
    assert docstring.yields.type_name == "int"
    assert docstring.yields.description == "description"
    assert docstring.yields.is_generator
    assert docstring.many_returns is not None
    assert len(docstring.many_returns) == 0


def test_raises() -> None:
    """Test parsing raises."""
    docstring = parse(
        """
        Short description
        """
    )
    assert len(docstring.raises) == 0

    docstring = parse(
        """
        Short description
        :raises: description
        """
    )
    assert len(docstring.raises) == 1
    assert docstring.raises[0].type_name is None
    assert docstring.raises[0].description == "description"

    docstring = parse(
        """
        Short description
        :raises ValueError: description
        """
    )
    assert len(docstring.raises) == 1
    assert docstring.raises[0].type_name == "ValueError"
    assert docstring.raises[0].description == "description"


def test_broken_meta() -> None:
    """Test parsing broken meta."""
    with pytest.raises(ParseError):
        parse(":")

    with pytest.raises(ParseError):
        parse(":param herp derp")

    with pytest.raises(ParseError):
        parse(":param: invalid")

    with pytest.raises(ParseError):
        parse(":param with too many args: desc")

    # these should not raise any errors
    parse(":sthstrange: desc")


def test_deprecation() -> None:
    """Test parsing deprecation notes."""
    docstring = parse(":deprecation: 1.1.0 this function will be removed")
    assert docstring.deprecation is not None
    assert docstring.deprecation.version == "1.1.0"
    assert docstring.deprecation.description == "this function will be removed"

    docstring = parse(":deprecation: this function will be removed")
    assert docstring.deprecation is not None
    assert docstring.deprecation.version is None
    assert docstring.deprecation.description == "this function will be removed"


@pytest.mark.parametrize(
    "rendering_style, expected",
    [
        (
            RenderingStyle.COMPACT,
            "Short description.\n"
            "\n"
            "Long description.\n"
            "\n"
            ":param int foo: a description\n"
            ":param int bar: another description\n"
            ":returns float: a return",
        ),
        (
            RenderingStyle.CLEAN,
            "Short description.\n"
            "\n"
            "Long description.\n"
            "\n"
            ":param int foo: a description\n"
            ":param int bar: another description\n"
            ":returns float: a return",
        ),
        (
            RenderingStyle.EXPANDED,
            "Short description.\n"
            "\n"
            "Long description.\n"
            "\n"
            ":param foo:\n"
            "    a description\n"
            ":type foo: int\n"
            ":param bar:\n"
            "    another description\n"
            ":type bar: int\n"
            ":returns:\n"
            "    a return\n"
            ":rtype: float",
        ),
    ],
)
def test_compose(rendering_style: RenderingStyle, expected: str) -> None:
    """Test compose"""

    docstring = parse(
        """
        Short description.

        Long description.

        :param int foo: a description
        :param int bar: another description
        :return float: a return
        """
    )
    assert compose(docstring, rendering_style=rendering_style) == expected


def test_short_rtype() -> None:
    """Test abbreviated docstring with only return type information."""
    string = "Short description.\n\n:rtype: float"
    docstring = parse(string)
    rendering_style = RenderingStyle.EXPANDED
    assert compose(docstring, rendering_style=rendering_style) == string


@pytest.mark.parametrize(
    "src, expected_size",
    [
        ('', 0),
        ('Some text', 1),
        ('Some text\nSome more text', 2),
        ('Some text\n\nSome more text', 2),
        ('Some text\n\nSome more text\n\nEven more text', 2),
        (
                """
                Short description.

                This is a longer description.

                Parameters
                ----------
                a: int
                    description
                b: int
                    description

                Returns
                -------
                int
                    The return value

                Yields
                ------
                str
                    The yielded value

                Raises
                ------
                ValueError
                    If something goes wrong.
                TypeError
                    If something else goes wrong.
                IOError
                    If something else goes wrong.
                """,
                2,  # because Google style parser can't parse other styles
        ),
        (
                """
                Parameters
                ----------
                a: int
                    description
                b: int
                    description

                Returns
                -------
                int
                    The return value

                Yields
                ------
                str
                    The yielded value

                Raises
                ------
                ValueError
                    If something goes wrong.
                TypeError
                    If something else goes wrong.
                IOError
                    If something else goes wrong.
                """,
                2,  # because the beginning is parsed into short/long description
        ),
        (
                """
                Short description.

                This is a longer description.

                Args:
                    a (int): description
                    b (int): description

                Returns:
                    int: The return value

                Yields:
                    str: The yielded value

                Raises:
                    ValueError: If something goes wrong.
                    TypeError: If something else goes wrong.
                    IOError: If something else goes wrong.
                """,
                2,  # because ReST style parser can't parse other styles
        ),
        (
                """
                Args:
                    a (int): description
                    b (int): description

                Returns:
                    int: The return value

                Yields:
                    str: The yielded value

                Raises:
                    ValueError: If something goes wrong.
                    TypeError: If something else goes wrong.
                    IOError: If something else goes wrong.
                """,
                2,  # because the beginning is parsed into short/long description
        ),
        (
                """
                Short description.

                This is a longer description.

                :param a: description
                :type a: int
                :param b: description
                :type b: int
                :returns: The return value
                :rtype: int
                :yield: The yielded value
                :rtype: str
                :raises ValueError: If something goes wrong.
                :raises TypeError: If something else goes wrong.
                :raises IOError: If something else goes wrong.
                """,
                72,
        ),
        (
                """
                :param a: description
                :type a: int
                :param b: description
                :type b: int
                :returns: The return value
                :rtype: int
                :yield: The yielded value
                :rtype: str
                :raises ValueError: If something goes wrong.
                :raises TypeError: If something else goes wrong.
                :raises IOError: If something else goes wrong.
                """,
                70,
        ),
    ],
)
def test_docstring_size(src: str, expected_size: int) -> None:
    docstring = parse(src)
    assert docstring.size == expected_size
