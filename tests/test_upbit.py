import pytest

from upbit import (
    ApiKeyError, Upbit
)


class TestUpbit:

    def test_request_wrapper(self):
        # upbit = _Upbit()
        # todo _request_wrapper
        pass

    @pytest.mark.parametrize(
        "access_key, secret_key",
        (
                (None, None),
                (None, "abcde"),
                ("abcde", None),
                ("", None),
                (None, ""),
                ("", ""),
        ),
    )
    def test_auth_guard(self, access_key, secret_key):
        with pytest.raises(ApiKeyError):

            @Upbit._auth_guard
            def func(self):
                pass
            Upbit.func = func

            up = Upbit(access_key=access_key, secret_key=secret_key)

            up.func()


