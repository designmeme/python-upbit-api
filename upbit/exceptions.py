"""
upbit.exceptions

Upbit API Error 공식 페이지 참고
- 요청 수 제한 (429)
    https://docs.upbit.com/docs/user-request-guide

- API 주요 에러 코드 목록 (400, 401)
    https://docs.upbit.com/docs/api-%EC%A3%BC%EC%9A%94-%EC%97%90%EB%9F%AC-%EC%BD%94%EB%93%9C-%EB%AA%A9%EB%A1%9D

    에러 발생시 JSON body 구조
    {
      "error": {
        "name": "<오류 코드>"
        "message": "<오류에 대한 설명>",
      }
    }
"""

from requests import HTTPError


class UpbitHTTPError(HTTPError):
    def __init__(self, msg: str, ex: HTTPError):
        # Invoke the super class's __init__
        super(UpbitHTTPError, self).__init__(msg, response=ex.response)


class UpbitClientError(UpbitHTTPError):
    """기타 업비트 클라이언트 에러 발생"""


class UpbitServerError(UpbitHTTPError):
    """기타 업비트 서버 에러 발생"""


class TooManyRequests(UpbitClientError):
    """429 요청 수 제한 초과 에러 발생"""


class CreateAskError(UpbitClientError):
    """400 매도 주문 요청 에러 발생"""


class CreateBidError(UpbitClientError):
    """400 매수 주문 요청 에러 발생"""


class InsufficientFundsAsk(UpbitClientError):
    """400 매도 가능 잔고 부족 에러 발생"""


class InsufficientFundsBid(UpbitClientError):
    """400 매수 가능 잔고 부족 에러 발생"""


class UnderMinTotalAsk(UpbitClientError):
    """400 최소주문금액 미만으로 매도 주문 요청 에러 발생"""


class UnderMinTotalBid(UpbitClientError):
    """400 최소주문금액 미만으로 매수 주문 요청 에러 발생"""


class WithdrawAddressNotRegistered(UpbitClientError):
    """400 미등록 출금 주소 에러 발생"""


class InvalidParameterError(UpbitClientError):
    """400 잘못된 요청 파라미터 에러 발생"""


class ValidationError(UpbitClientError):
    """400 잘못된 API 요청 에러 발생"""


class InvalidQueryPayload(UpbitClientError):
    """401 JWT 헤더 페이로드 에러 발생"""


class JwtVerification(UpbitClientError):
    """401 JWT 헤더 검증 에러 발생"""


class ExpiredAccessKey(UpbitClientError):
    """401 API 키 만료 에러 발생"""


class NonceUsed(UpbitClientError):
    """401 논스 재사용 에러 발생"""


class NoAuthorizationIP(UpbitClientError):
    """401 미등록 IP 에러 발생"""


class OutOfScope(UpbitClientError):
    """401 허용되지 않은 기능 에러 발생"""


class ApiKeyError(Exception):
    """access_key 혹은 secret_key 누락 에러 발생"""


class InvalidRemainingReq(Exception):
    """규격에 맞지 않는 Remaining-Req 헤더값 에러 발생"""


_ERROR_EXCEPTION_DICT = {
    "create_ask_error": CreateAskError,
    "create_bid_error": CreateBidError,
    "insufficient_funds_ask": InsufficientFundsAsk,
    "insufficient_funds_bid": InsufficientFundsBid,
    "under_min_total_ask": UnderMinTotalAsk,
    "under_min_total_bid": UnderMinTotalBid,
    "withdraw_address_not_registerd": WithdrawAddressNotRegistered,
    "invalid_parameter": InvalidParameterError,
    "validation_error": ValidationError,
    "invalid_query_payload": InvalidQueryPayload,
    "jwt_verification": JwtVerification,
    "expired_access_key": ExpiredAccessKey,
    "nonce_used": NonceUsed,
    "no_authorization_i_p": NoAuthorizationIP,
    "out_of_scope": OutOfScope,
}
"""Upbit API 오류 코드와 1:1로 맞춘 UpbitHTTPError 예외 클래스를 담은 딕셔너리"""
