from collections.abc import Iterator

import pytest

from yukilog import shutdown


@pytest.fixture(autouse=True)
def reset_yukilog() -> Iterator[None]:
    shutdown()
    yield
    shutdown()
