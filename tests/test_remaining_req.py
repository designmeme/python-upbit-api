import datetime

import pytest

import upbit as _upbit


def test_remaining_req_class():
    remaining_req = 'group=candles; min=60; sec=10'
    instance = _upbit.RemainingReq(remaining_req)
    assert instance.group == 'candles'
    assert instance.minute == 60
    assert instance.second == 10
    assert isinstance(instance.updated, datetime.datetime)


def test_remaining_req_class_value_error():
    with pytest.raises(_upbit.RemainingReqValueError):
        _upbit.RemainingReq('')

    with pytest.raises(_upbit.RemainingReqValueError):
        _upbit.RemainingReq('group=candles; min=60')

    with pytest.raises(_upbit.RemainingReqValueError):
        _upbit.RemainingReq('group=candles; min=60; sec=')


def test_remaining_req_cache():
    upbit = _upbit.Upbit()
    assert upbit.get_remaining_reqs('market') is None

    upbit.get_markets()
    assert isinstance(upbit.get_remaining_reqs('market'), _upbit.RemainingReq)
