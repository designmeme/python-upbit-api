import pytest
import requests_mock

from upbit import (
    Upbit,
    TooManyRequests,
    CreateAskError,
    CreateBidError,
    InsufficientFundsAsk,
    InsufficientFundsBid,
    UnderMinTotalAsk,
    UnderMinTotalBid,
    WithdrawAddressNotRegistered,
    InvalidParameterError,
    ValidationError,
    InvalidQueryPayload,
    JwtVerification,
    ExpiredAccessKey,
    NonceUsed,
    NoAuthorizationIP,
    OutOfScope,
    ApiKeyError,
    UpbitClientError,
    UpbitServerError,
)


class TestUpbit:

    @pytest.mark.parametrize(
        "exception, status_code, error_code",
        (
            (TooManyRequests, 429, None),
            (CreateAskError, 400, "create_ask_error"),
            (CreateBidError, 400, "create_bid_error"),
            (InsufficientFundsAsk, 400, "insufficient_funds_ask"),
            (InsufficientFundsBid, 400, "insufficient_funds_bid"),
            (UnderMinTotalAsk, 400, "under_min_total_ask"),
            (UnderMinTotalBid, 400, "under_min_total_bid"),
            (WithdrawAddressNotRegistered, 400, "withdraw_address_not_registerd"),
            (InvalidParameterError, 400, "invalid_parameter"),
            (ValidationError, 400, "validation_error"),
            (InvalidQueryPayload, 401, "invalid_query_payload"),
            (JwtVerification, 401, "jwt_verification"),
            (ExpiredAccessKey, 401, "expired_access_key"),
            (NonceUsed, 401, "nonce_used"),
            (NoAuthorizationIP, 401, "no_authorization_i_p"),
            (OutOfScope, 401, "out_of_scope"),
            (UpbitClientError, 401, "not_in_doc_error"),
            (UpbitClientError, 402, None),
            (UpbitServerError, 500, None),
        ),
    )
    def test_http_error(self, exception, status_code, error_code):
        with requests_mock.Mocker() as mock:
            json_body = {'error': {'name': error_code}} if error_code else None
            mock.get(requests_mock.ANY, status_code=status_code, json=json_body)

            with pytest.raises(exception):
                upbit = Upbit()
                upbit.get_markets()

    def test_json_error(self):
        with requests_mock.Mocker() as mock:
            mock.get(requests_mock.ANY, status_code=401, text='not json body')

            with pytest.raises(UpbitClientError):
                upbit = Upbit()
                upbit.get_markets()

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
        with requests_mock.Mocker() as mock:
            mock.get(requests_mock.ANY)

            with pytest.raises(ApiKeyError):
                up = Upbit(access_key=access_key, secret_key=secret_key)
                up.get_accounts()

    def test_auth_header(self):
        upbit = Upbit('xxxxx', 'xxxxx')
        auth_headers = upbit._get_request_headers(None, {'test': 123})

        assert auth_headers.get('Authorization') is not None
        assert auth_headers.get('test') == 123
