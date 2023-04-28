import pytest

import upbit as _upbit


def test_request_wrapper():
    upbit = _upbit.Upbit()
    # todo _request_wrapper


def test_auth_guard():
    # todo use mock
    with pytest.raises(_upbit.ApiKeyError):
        upbit = _upbit.Upbit()
        upbit.get_accounts()

    with pytest.raises(_upbit.ApiKeyError):
        upbit = _upbit.Upbit(access_key='abc', secret_key=None)
        upbit.get_accounts()

    with pytest.raises(_upbit.ApiKeyError):
        upbit = _upbit.Upbit(access_key=None, secret_key='abc')
        upbit.get_accounts()
