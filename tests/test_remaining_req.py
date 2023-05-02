import datetime

import pytest

import upbit as _upbit
from upbit import RemainingReq, InvalidRemainingReq


def test_remaining_req_class():
    remaining_req = 'group=candles; min=60; sec=10'
    instance = RemainingReq(remaining_req)
    assert instance.group == 'candles'
    assert instance.minute == 60
    assert instance.second == 10
    assert isinstance(instance.updated, datetime.datetime)


@pytest.mark.parametrize(
    "exception, remaining_req",
    (
        (InvalidRemainingReq, ""),
        (InvalidRemainingReq, "group=candles; min=60"),
        (InvalidRemainingReq, "group=candles; min=60; sec="),
    ),
)
def test_invalid_remaining_req(exception, remaining_req):
    with pytest.raises(exception):
        RemainingReq(remaining_req)


def test_remaining_req_cache():
    upbit = _upbit.Upbit()
    assert upbit.get_remaining_reqs('market') is None

    # todo mock
    upbit.get_markets()
    assert isinstance(upbit.get_remaining_reqs('market'), RemainingReq)
