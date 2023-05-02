import datetime

import pytest

from upbit import RemainingReq, InvalidRemainingReq, Upbit


class TestRemainingReq:
    def test_property(self):
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
    def test_invalid_remaining_req(self, exception, remaining_req):
        with pytest.raises(exception):
            RemainingReq(remaining_req)

    def test_remaining_req_cache(self):
        up = Upbit()
        assert up.get_remaining_reqs('market') is None

        # todo mock
        up.get_markets()
        assert isinstance(up.get_remaining_reqs('market'), RemainingReq)
