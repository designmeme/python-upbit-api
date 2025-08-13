from __future__ import annotations

import functools
import hashlib
import logging
import uuid as _uuid
from typing import Any, Optional, Literal, Dict, Callable, Tuple, List, Union
from urllib.parse import urlencode, unquote

import jwt
import requests
from requests import Response
from requests.adapters import HTTPAdapter
from typing_extensions import deprecated

from .exceptions import (
    _ERROR_EXCEPTION_DICT,
    TooManyRequests,
    UpbitServerError,
    UpbitClientError,
    ApiKeyError,
    InvalidRemainingReq,
)
from .models import (
    OrderBy,
    OrderState,
    OrderSide,
    OrderType,
    WithdrawState,
    DepositState,
    TwoFactorType,
    TransactionType,
    MinuteUnit,
    RequestGroup,
    RemainingReq, OpenOrderState, ClosedOrderState,
)


class Upbit:
    def __init__(self,
                 access_key: Optional[str] = None,
                 secret_key: Optional[str] = None,
                 http_adapter: Optional[HTTPAdapter] = None,
                 timeout: Union[float, Tuple[float, float], Tuple[float, None]] = None,
                 ):
        """
        :param access_key: 업비트 API Access Key
        :param secret_key: 업비트 API Secret Key
        :param http_adapter: 업비트 API 호출용 `requests.Session` 에 설정 할 HTTPAdapter
        :param timeout: 업비트 API 호출시 `requests.Session.request` 의 기본 timeout 설정값 (connect, read)

        .. note::
            - Quotation API만 사용한다면 access_key, secret_key를 설정하지 않아도 됩니다.
            - Exchange API를 사용하려면 access_key, secret_key를 필수로 설정해야 합니다.
            - 업비트 서버 점검시 연결 되지 않으며 커넥션이 무한 대기 상태가 됩니다. 이를 방지를 위해 적절한 timout 값을 설정하길 권장합니다. `Requests Timeouts 참고 <https://requests.readthedocs.io/en/latest/user/advanced/#timeouts>`_
        """

        self._endpoint = "https://api.upbit.com/v1"

        self._access_key = access_key
        self._secret_key = secret_key

        # 요청 그룹별 잔여 요청수를 저장할 딕셔너리
        # - 키: group 명 / 값: RemainingReq 인스턴스
        self._remaining_reqs: Dict[RequestGroup, RemainingReq] = {}

        # Requests Session 인스턴스 사용하여 모든 요청을 처리함.
        self._session = requests.Session()

        if http_adapter and isinstance(http_adapter, HTTPAdapter):
            self._session.mount(self._endpoint, http_adapter)

        self._session.request = functools.partial(self._session.request, timeout=timeout)

        self._logger = logging.getLogger(__name__)

    def _request_wrapper(func: Callable) -> Callable:
        """
        업비트 API 요청 래퍼

        1) 잔여 요청수 처리
        2) HTTPError를 UpbitError로 변환

        :raises upbit.exceptions.TooManyRequests: 상태 코드가 429인 경우 발생
        :raises upbit.exceptions.CreateAskError: 상태 코드가 400이고 인 오류 코드가 'create_ask_error' 인 경우 발생
        :raises upbit.exceptions.CreateBidError: 상태 코드가 400이고 인 오류 코드가 'create_bid_error' 인 경우 발생
        :raises upbit.exceptions.InsufficientFundsAsk: 상태 코드가 400이고 인 오류 코드가 'insufficient_funds_ask' 인 경우 발생
        :raises upbit.exceptions.InsufficientFundsBid: 상태 코드가 400이고 인 오류 코드가 'insufficient_funds_bid' 인 경우 발생
        :raises upbit.exceptions.UnderMinTotalAsk: 상태 코드가 400이고 인 오류 코드가 'under_min_total_ask' 인 경우 발생
        :raises upbit.exceptions.UnderMinTotalAsk: 상태 코드가 400이고 인 오류 코드가 'under_min_total_ask' 인 경우 발생
        :raises upbit.exceptions.UnderMinTotalBid: 상태 코드가 400이고 인 오류 코드가 'under_min_total_bid' 인 경우 발생
        :raises upbit.exceptions.WithdrawAddressNotRegistered: 상태 코드가 400이고 인 오류 코드가 'withdraw_address_not_registerd' 인 경우 발생
        :raises upbit.exceptions.InvalidParameterError: 상태 코드가 400이고 인 오류 코드가 'invalid_parameter' 인 경우 발생
        :raises upbit.exceptions.ValidationError: 상태 코드가 400이고 인 오류 코드가 'validation_error' 인 경우 발생
        :raises upbit.exceptions.InvalidQueryPayload: 상태 코드가 401이고 인 오류 코드가 'invalid_query_payload' 인 경우 발생
        :raises upbit.exceptions.JwtVerification: 상태 코드가 401이고 인 오류 코드가 'jwt_verification' 인 경우 발생
        :raises upbit.exceptions.ExpiredAccessKey: 상태 코드가 401이고 인 오류 코드가 'expired_access_key' 인 경우 발생
        :raises upbit.exceptions.NonceUsed: 상태 코드가 401이고 인 오류 코드가 'nonce_used' 인 경우 발생
        :raises upbit.exceptions.NoAuthorizationIP: 상태 코드가 401이고 인 오류 코드가 'no_authorization_i_p' 인 경우 발생
        :raises upbit.exceptions.OutOfScope: 상태 코드가 401이고 인 오류 코드가 'out_of_scope' 인 경우 발생
        :raises upbit.exceptions.UpbitClientError: 이 외에 상태 코드가 400 이상, 500 미만인 경우 발생
        :raises upbit.exceptions.UpbitServerError: 상태 코드가 500 이상, 600 미만인 경우 발생
        """

        @functools.wraps(func)
        def wrapper(self, *args: Any, **kwargs: Dict[str, Any]) -> Response:
            remaining_req: Optional[RemainingReq] = None

            try:
                response: Response = func(self, *args, **kwargs)

                # 잔여 요청수 기록
                remaining_req = self._process_remaining_req(response.headers.get("Remaining-Req"))

                # status code가 400~600 일 때 예외 발생시키기
                response.raise_for_status()

                return response
            except requests.HTTPError as e:
                status_code = e.response.status_code
                reason = e.response.reason
                url = e.response.url
                error_msg = f"{status_code} Client Error: {reason} for url: {url}"

                # TooManyRequests 에러 처리
                if status_code == 429:
                    # 이 에러는 규격화된 Upbit 에러 JSON 바디를 갖지 않음.
                    raise TooManyRequests(error_msg, e)

                # Upbit API 주요 에러 코드 목록에 명시된 에러 처리
                elif status_code in [400, 401]:
                    try:
                        # 에러 코드와 맞는 예외를 찾아 발생시킨다.
                        error_body = e.response.json()["error"]
                        error_code = error_body.get("name")
                        error_msg = error_body.get("message")
                        error_exception = _ERROR_EXCEPTION_DICT.get(error_code)

                        reason = error_msg
                        if error_exception:
                            raise error_exception(error_msg, e)
                        else:
                            # 명시되지 않은 에러가 발생한 경우
                            raise UpbitClientError(error_msg, e)
                    # body 내용이 json 형태가 아닌 경우
                    except requests.JSONDecodeError:
                        raise UpbitClientError(error_msg, e)

                # 기타 Upbit Client error 처리
                elif 400 <= status_code < 500:
                    raise UpbitClientError(error_msg, e)

                # Upbit Server error 처리
                elif 500 <= status_code < 600:
                    raise UpbitServerError(f"{status_code} Server Error: {reason} for url: {url}", e)

        return wrapper

    @_request_wrapper
    def _request(self, method: str, url: str, **kwargs) -> Response:
        return self._session.request(method, url, **kwargs)

    def _process_remaining_req(self, remaining_req: str) -> Optional[RemainingReq]:
        """Remaining-Req 응답 헤더를 캐시하고 RemainingReq 인스턴스로 변환하여 반환한다.

        :param remaining_req: Remaining-Req 응답 헤더값

        :return: RemainingReq 인스턴스
        """
        try:
            rr = RemainingReq(remaining_req)
            self._remaining_reqs[rr.group] = rr
            self._logger.debug(f"Upbit API 잔여 요청수 {rr}")
            return rr
        except InvalidRemainingReq as e:
            self._logger.warning(f"Upbit API 잔여 요청수 처리 InvalidRemainingReq. {e!r}")
            pass
        except Exception as e:
            self._logger.warning(f"Upbit API 잔여 요청수 처리 에러. {remaining_req=!r} {e!r}")
            pass

    def _get_request_headers(self, query: dict = None, headers: dict = None) -> Dict:
        """인증 헤더를 만들어 반환한다.

        :param query: 요청 바디
        :param headers: 기존 요청 헤더
        :return: 기존 요청 헤더에 인증 헤더를 추가해서 반환

        :raises upbit.exceptions.ApiKeyError: 인증 키 정보가 없을 때 발생
        """

        if not self._access_key or not self._secret_key:
            raise ApiKeyError(f'인증 정보가 필요합니다.')

        payload = {
            "access_key": self._access_key,
            "nonce": str(_uuid.uuid4())
        }

        if query is not None:
            query = {k: v for k, v in query.items() if v is not None}
            query_string = unquote(urlencode(query, doseq=True)).encode("utf-8")
            m = hashlib.sha512()
            m.update(query_string)
            query_hash = m.hexdigest()
            payload['query_hash'] = query_hash
            payload['query_hash_alg'] = "SHA512"

        jwt_token = jwt.encode(payload, self._secret_key)
        authorization_token = 'Bearer {}'.format(jwt_token)

        if headers is None:
            headers = {}
        headers['Authorization'] = authorization_token
        return headers

    def get_remaining_reqs(self, group: RequestGroup) -> Optional[RemainingReq]:
        """그룹의 잔여 요청수 정보 반환

        :param group: RequestGroup 잔여 요청 그룹

        :return: RemainingReq 잔여 요청 정보. 이전 응답 헤더에서 얻은 정보를 저장해 놓은 가장 최신 정보.

        Usage::

            upbit = Upbit()
            res = upbit.get_candles_day('KRW-BTC')
            rr = upbit.get_remaining_reqs('candles')

        """
        return self._remaining_reqs.get(group)

    # --------------------------------------------------------------------------
    # Exchange API > 자산
    # --------------------------------------------------------------------------

    def get_accounts(self,
                     **kwargs) -> Response:
        """전체 계좌 조회

        내가 보유한 자산 리스트를 보여줍니다.

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EC%A0%84%EC%B2%B4-%EA%B3%84%EC%A2%8C-%EC%A1%B0%ED%9A%8C>`_

        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.get_accounts()
            print(res.json())

            [{
                'currency': 'KRW',
                'balance': '628906.97823303',
                'locked': '0',
                'avg_buy_price': '0',
                'avg_buy_price_modified': True,
                'unit_currency': 'KRW'
            }, {
                'currency': 'ELF',
                'balance': '1142.57511675',
                'locked': '0',
                'avg_buy_price': '292.6613',
                'avg_buy_price_modified': False,
                'unit_currency': 'KRW'
            }, ...]
        """
        url = self._endpoint + "/accounts"
        headers = self._get_request_headers(headers=kwargs.pop('headers', None))

        return self._request('get', url, headers=headers, **kwargs)

    # --------------------------------------------------------------------------
    # Exchange API > 주문
    # --------------------------------------------------------------------------

    def get_order_chance(self,
                         market: str,
                         **kwargs) -> Response:
        """주문 가능 정보 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EC%A3%BC%EB%AC%B8-%EA%B0%80%EB%8A%A5-%EC%A0%95%EB%B3%B4>`_

        :param market: 마켓 코드 (ex. KRW-BTC)
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.get_order_chance('KRW-BTC')
            print(res.json())

            {'ask_account': {'avg_buy_price': '28560783.8337',
                             'avg_buy_price_modified': False,
                             'balance': '0',
                             'currency': 'BTC',
                             'locked': '0',
                             'unit_currency': 'KRW'},
             'ask_fee': '0.0005',
             'bid_account': {'avg_buy_price': '0',
                             'avg_buy_price_modified': True,
                             'balance': '628906.97823303',
                             'currency': 'KRW',
                             'locked': '0',
                             'unit_currency': 'KRW'},
             'bid_fee': '0.0005',
             'maker_ask_fee': '0.0005',
             'maker_bid_fee': '0.0005',
             'market': {'ask': {'currency': 'BTC', 'min_total': '5000'},
                        'ask_types': ['limit', 'market'],
                        'bid': {'currency': 'KRW', 'min_total': '5000'},
                        'bid_types': ['limit', 'price'],
                        'id': 'KRW-BTC',
                        'max_total': '1000000000',
                        'name': 'BTC/KRW',
                        'order_sides': ['ask', 'bid'],
                        'order_types': ['limit'],
                        'state': 'active'}}
        """
        url = self._endpoint + "/orders/chance"
        params = {
            "market": market,
        }
        headers = self._get_request_headers(params, headers=kwargs.pop('headers', None))

        return self._request('get', url, headers=headers, params=params, **kwargs)

    def get_order(self,
                  *,
                  uuid: Optional[str] = None,
                  identifier: Optional[str] = None,
                  **kwargs) -> Response:
        """개별 주문 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EA%B0%9C%EB%B3%84-%EC%A3%BC%EB%AC%B8-%EC%A1%B0%ED%9A%8C>`_

        .. note:: uuid 혹은 identifier 둘 중 하나의 값이 반드시 포함되어야 합니다.

        :param uuid: 주문 UUID
        :param identifier: 조회용 사용자 지정 값
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.get_order(uuid='d7c96420-a9ab-4ae8-a461-3db412427fb3')
            print(res.json())

            {
                'created_at': '2023-02-06T11:00:45+09:00',
                'executed_volume': '132.99843443',
                'locked': '0',
                'market': 'KRW-STRAX',
                'ord_type': 'market',
                'paid_fee': '50.738902735045',
                'remaining_fee': '0',
                'remaining_volume': '0',
                'reserved_fee': '0',
                'side': 'ask',
                'state': 'done',
                'trades': [{'created_at': '2023-02-06T11:00:44+09:00',
                         'funds': '101477.80547009',
                         'market': 'KRW-STRAX',
                         'price': '763',
                         'side': 'ask',
                         'trend': 'down',
                         'uuid': '3f818e33-e8be-495c-a62f-f7697735f2bd',
                         'volume': '132.99843443'}],
                'trades_count': 1,
                'uuid': 'd7c96420-a9ab-4ae8-a461-3db412427fb3',
                'volume': '132.99843443'
            }
        """
        url = self._endpoint + "/order"
        params = {
            "uuid": uuid,
            "identifier": identifier,
        }
        headers = self._get_request_headers(params, headers=kwargs.pop('headers', None))

        return self._request('get', url, headers=headers, params=params, **kwargs)

    def get_orders(self,
                   *,
                   market: str = None,
                   uuids: List[str] = None,
                   identifiers: List[str] = None,
                   state: OrderState = 'wait',
                   states: List[OrderState] = None,
                   page: int = 1,
                   limit: int = 100,
                   order_by: OrderBy = 'desc',
                   **kwargs) -> Response:
        """주문 리스트 조회 - Deprecated (2024.06~)

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EC%A3%BC%EB%AC%B8-%EB%A6%AC%EC%8A%A4%ED%8A%B8-%EC%A1%B0%ED%9A%8C>`_

        :param market: 마켓 코드 (ex. KRW-BTC)
        :param uuids: 주문 UUID 리스트
        :param identifiers: 주문 identifier 리스트
        :param state: 주문 상태
        :param states: 주문 상태 리스트
        :param page: 페이지 수
        :param limit: 요청 개수
        :param order_by: 정렬 방식
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.get_orders(market='KRW-ELF', state='done')
            print(res.json())

            [{
                'created_at': '2023-02-15T08:00:40+09:00',
                'executed_volume': '380.4181703',
                'locked': '0',
                'market': 'KRW-ELF',
                'ord_type': 'market',
                'paid_fee': '56.6823073747',
                'remaining_fee': '0',
                'remaining_volume': '0',
                'reserved_fee': '0',
                'side': 'ask',
                'state': 'done',
                'trades_count': 1,
                'uuid': 'd5c96aeb-b519-46a8-bb79-f694e40acc71',
                'volume': '380.4181703'
            }, ...]
        """
        url = self._endpoint + "/orders"
        params = {
            "market": market,
            "uuids[]": uuids,
            "identifiers[]": identifiers,
            "state": state,
            "states[]": states,
            "page": page,
            "limit": limit,
            "order_by": order_by,
        }
        headers = self._get_request_headers(params, headers=kwargs.pop('headers', None))

        return self._request('get', url, headers=headers, params=params, **kwargs)

    def get_orders_by_id(self,
                         *,
                         market: Optional[str] = None,
                         uuids: Optional[List[str]] = None,
                         identifiers: Optional[List[str]] = None,
                         order_by: OrderBy = 'desc',
                         **kwargs) -> Response:
        """id로 주문리스트 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/id%EB%A1%9C-%EC%A3%BC%EB%AC%B8-%EC%A1%B0%ED%9A%8C>`_

        :param market: 마켓 코드 (ex. KRW-BTC)
        :param uuids: 주문 UUID 리스트
        :param identifiers: 주문 identifier 리스트
        :param order_by: 정렬 방식
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.get_orders_by_id(uuids=['xxxxxxxx'])
            print(res.json())

            [{
                "uuid": "d098ceaf-6811-4df8-97f2-b7e01aefc03f",
                "side": "bid",
                "ord_type": "limit",
                "price": "104812000",
                "state": "wait",
                "market": "KRW-BTC",
                "created_at": "2024-06-13T10:26:21+09:00",
                "volume": "0.00101749",
                "remaining_volume": "0.00006266",
                "reserved_fee": "53.32258094",
                "remaining_fee": "3.28375996",
                "paid_fee": "50.03882098",
                "locked": "6570.80367996",
                "executed_volume": "0.00095483",
                "executed_funds": "100077.64196",
                "trades_count": 1
            }, ...]
        """
        url = self._endpoint + "/orders/uuids"
        params = {
            "market": market,
            "uuids[]": uuids,
            "identifiers[]": identifiers,
            "order_by": order_by,
        }
        headers = self._get_request_headers(params, headers=kwargs.pop('headers', None))

        return self._request('get', url, headers=headers, params=params, **kwargs)

    def get_open_orders(self,
                        *,
                        market: Optional[str] = None,
                        state: OpenOrderState = 'wait',
                        states: Optional[List[OpenOrderState]] = None,
                        page: int = 1,
                        limit: int = 100,
                        order_by: OrderBy = 'desc',
                        **kwargs) -> Response:
        """체결 대기 주문 (Open Order) 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EB%8C%80%EA%B8%B0-%EC%A3%BC%EB%AC%B8-%EC%A1%B0%ED%9A%8C>`_

        :param market: 마켓 코드 (ex. KRW-BTC)
        :param state: 주문 상태
        :param states: 주문 상태 리스트
        :param page: 페이지 수
        :param limit: 요청 개수
        :param order_by: 정렬 방식
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.get_open_orders(market='KRW-BTC', state='wait')
            print(res.json())

            [{
                "uuid": "d098ceaf-6811-4df8-97f2-b7e01aefc03f",
                "side": "bid",
                "ord_type": "limit",
                "price": "104812000",
                "state": "wait",
                "market": "KRW-BTC",
                "created_at": "2024-06-13T10:26:21+09:00",
                "volume": "0.00101749",
                "remaining_volume": "0.00006266",
                "reserved_fee": "53.32258094",
                "remaining_fee": "3.28375996",
                "paid_fee": "50.03882098",
                "locked": "6570.80367996",
                "executed_volume": "0.00095483",
                "executed_funds": "100077.64196",
                "trades_count": 1
            }, ...]
        """
        url = self._endpoint + "/orders/open"
        params = {
            "market": market,
            "state": state,
            "states[]": states,
            "page": page,
            "limit": limit,
            "order_by": order_by,
        }
        headers = self._get_request_headers(params, headers=kwargs.pop('headers', None))

        return self._request('get', url, headers=headers, params=params, **kwargs)

    def get_closed_orders(self,
                          *,
                          market: Optional[str] = None,
                          state: ClosedOrderState | None = None,
                          states: Optional[List[ClosedOrderState]] = None,
                          start_time: Optional[str] = None,
                          end_time: Optional[str] = None,
                          limit: int = 100,
                          order_by: OrderBy = 'desc',
                          **kwargs) -> Response:
        """종료된 주문 (Closed Order) 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EC%A2%85%EB%A3%8C-%EC%A3%BC%EB%AC%B8-%EC%A1%B0%ED%9A%8C>`_

        :param market: 마켓 코드 (ex. KRW-BTC)
        :param state: 주문 상태
        :param states: 주문 상태 리스트
        :param start_time: 조회 시작 시간 (주문 생성시간 기준)
        :param end_time: 조회 종료 시간 (주문 생성시간 기준)
        :param limit: 요청 개수
        :param order_by: 정렬 방식
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.get_closed_orders(market='KRW-BTC', state='done')
            print(res.json())

            [{
                "uuid": "e5715c44-2d1a-41e6-91d8-afa579e28731",
                "side": "ask",
                "ord_type": "limit",
                "price": "103813000",
                "state": "done",
                "market": "KRW-BTC",
                "created_at": "2024-06-13T10:28:36+09:00",
                "volume": "0.00039132",
                "remaining_volume": "0",
                "reserved_fee": "0",
                "remaining_fee": "0",
                "paid_fee": "20.44627434",
                "locked": "0",
                "executed_volume": "0.00039132",
                "executed_funds": "40892.54868",
                "trades_count": 2
            }, ...]
        """
        url = self._endpoint + "/orders/closed"
        params = {
            "market": market,
            "state": state,
            "states[]": states,
            "start_time": start_time,
            "end_time": end_time,
            "limit": limit,
            "order_by": order_by,
        }
        headers = self._get_request_headers(params, headers=kwargs.pop('headers', None))

        return self._request('get', url, headers=headers, params=params, **kwargs)

    def delete_order(self,
                     *,
                     uuid: Optional[str] = None,
                     identifier: Optional[str] = None,
                     **kwargs) -> Response:
        """주문 취소 접수

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EC%A3%BC%EB%AC%B8-%EC%B7%A8%EC%86%8C>`_

        .. note:: uuid 혹은 identifier 둘 중 하나의 값이 반드시 포함되어야 합니다.

        :param uuid: 주문 UUID
        :param identifier: 조회용 사용자 지정 값
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.delete_order(uuid='cdd92199-2897-4e14-9448-f923320408ad')
            print(res.json())

            {
                "uuid": "cdd92199-2897-4e14-9448-f923320408ad",
                "side": "bid",
                "ord_type": "limit",
                "price": "100.0",
                "state": "wait",
                "market": "KRW-BTC",
                "created_at": "2018-04-10T15:42:23+09:00",
                "volume": "0.01",
                "remaining_volume": "0.01",
                "reserved_fee": "0.0015",
                "remaining_fee": "0.0015",
                "paid_fee": "0.0",
                "locked": "1.0015",
                "executed_volume": "0.0",
                "trades_count": 0
            }
        """
        url = self._endpoint + "/order"
        params = {
            "uuid": uuid,
            "identifier": identifier,
        }
        headers = self._get_request_headers(params, headers=kwargs.pop('headers', None))

        return self._request('delete', url, headers=headers, params=params, **kwargs)

    def delete_orders(
            self,
            *,
            cancel_side: Literal['all', 'ask', 'bid'] = 'all',
            pairs: List[str] = None,
            excluded_pairs: List[str] = None,
            quote_currencies: List[str] = None,
            count: int = 20,
            order_by: OrderBy = 'desc',
            **kwargs) -> Response:
        """주문 일괄 취소 접수

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EC%A3%BC%EB%AC%B8-%EC%9D%BC%EA%B4%84-%EC%B7%A8%EC%86%8C-%EC%A0%91%EC%88%98>`_

        :param cancel_side: 주문 종류
        :param pairs: 취소할 마켓 코드 리스트 (ex. ["KRW-BTC"])
        :param excluded_pairs: 제외할 마켓 코드 리스트 (ex. ["KRW-BTC"])
        :param quote_currencies: 취소할 거래 화폐 리스트 (ex. ["KRW", "BTC"])
        :param count: 취소 접수할 주문의 최대 개수 (default : 20, max : 300)
        :param order_by: 정렬 방식
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.delete_orders(cancel_side='all')
            print(res.json())

            {
              "success": {
                "count": 2,
                "orders": [
                  {
                    "uuid": "bbbb8e07-1689-4769-af3e-a117016623f8",
                    "market": "KRW-ETH"
                  },
                  {
                    "uuid": "4312ba49-5f1a-4a01-9f3b-2d2bce17267e",
                    "market": "KRW-ETH"
                  }
                ]
              },
              "failed": {
                "count": 1,
                "orders": [
                  {
                    "uuid": "bdb49a54-de36-4eb4-a963-9c8d4337a9da",
                    "market": "BTC-XRP"
                  }
                ]
              }
            }
        """
        url = self._endpoint + "/orders/open"
        params = {
            "cancel_side": cancel_side,
            "pairs": pairs,
            "excluded_pairs": excluded_pairs,
            "quote_currencies": quote_currencies,
            "count": count,
            "order_by": order_by,
        }
        headers = self._get_request_headers(params, headers=kwargs.pop('headers', None))

        return self._request('delete', url, headers=headers, params=params, **kwargs)

    def delete_orders_by_id(
            self,
            *,
            uuids: Optional[List[str]] = None,
            identifiers: Optional[List[str]] = None,
            **kwargs) -> Response:
        """id로 주문리스트 취소 접수

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/id%EB%A1%9C-%EC%A3%BC%EB%AC%B8%EB%A6%AC%EC%8A%A4%ED%8A%B8-%EC%B7%A8%EC%86%8C-%EC%A0%91%EC%88%98>`_

        .. note:: uuids 또는 identifiers 중 한 가지 필드는 필수이며, 두 가지 필드를 함께 사용할 수 없습니다.

        :param uuids: 취소할 주문 UUID의 목록 (최대 20개)
        :param identifiers: 취소할 주문 identifier의 목록 (최대 20개)
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.delete_orders_by_id(uuids=['6c1eac69-b9bc-4fbf-9982-e9c4641c453f'])
            print(res.json())

            {
              "success": {
                "count": 1,
                "orders": [
                  {
                    "uuid": "6c1eac69-b9bc-4fbf-9982-e9c4641c453f",
                    "market": "BTC-ADA"
                  },
                ]
              },
              "failed": {
                "count": 0,
                "orders": []
              }
            }
        """
        url = self._endpoint + "/orders/uuids"
        params = {
            "uuids": uuids,
            "identifiers": identifiers,
        }
        headers = self._get_request_headers(params, headers=kwargs.pop('headers', None))

        return self._request('delete', url, headers=headers, params=params, **kwargs)

    def create_order(self,
                     market: str,
                     side: OrderSide,
                     ord_type: OrderType,
                     *,
                     volume: Optional[str] = None,
                     price: Optional[str] = None,
                     identifier: Optional[str] = None,
                     **kwargs) -> Response:
        """주문하기

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EC%A3%BC%EB%AC%B8%ED%95%98%EA%B8%B0>`_

        :param market: 마켓 코드 (ex. KRW-BTC)
        :param side: 주문 종류 - bid(매수), ask(매도)
        :param ord_type: 주문 타입 - limit(지정가), price(시장가 매수), market(시장가 매도)
        :param volume: 주문량 (지정가, 시장가 매도 시 필수)
        :param price: 주문 가격 (지정가, 시장가 매수 시 필수)
        :param identifier: 조회용 사용자 지정 값
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.create_order(market='KRW-BTC', side='bid', ord_type='limit', price='100', volume='0.01')
            print(res.json())

            {
                "uuid": "cdd92199-2897-4e14-9448-f923320408ad",
                "side": "bid",
                "ord_type": "limit",
                "price": "100.0",
                "avg_price": "0.0",
                "state": "wait",
                "market": "KRW-BTC",
                "created_at": "2018-04-10T15:42:23+09:00",
                "volume": "0.01",
                "remaining_volume": "0.01",
                "reserved_fee": "0.0015",
                "remaining_fee": "0.0015",
                "paid_fee": "0.0",
                "locked": "1.0015",
                "executed_volume": "0.0",
                "trades_count": 0
            }
        """
        url = self._endpoint + "/orders"
        params = {
            "market": market,
            "side": side,
            "volume": volume,
            "price": price,
            "ord_type": ord_type,
            "identifier": identifier,
        }
        headers = self._get_request_headers(params, headers=kwargs.pop('headers', None))

        return self._request('post', url, headers=headers, params=params, **kwargs)

    # --------------------------------------------------------------------------
    # Exchange API > 출금
    # --------------------------------------------------------------------------

    def get_withdraws(self,
                      *,
                      currency: Optional[str] = None,
                      state: Optional[WithdrawState] = None,
                      uuids: Optional[List[str]] = None,
                      txids: Optional[List[str]] = None,
                      page: int = 1,
                      limit: int = 100,
                      order_by: OrderBy = 'desc',
                      **kwargs) -> Response:
        """출금 리스트 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EC%A0%84%EC%B2%B4-%EC%B6%9C%EA%B8%88-%EC%A1%B0%ED%9A%8C>`_

        :param currency: Currency 코드
        :param state: 출금 상태
        :param uuids: 출금 UUID 리스트
        :param txids: 출금 TXID 리스트
        :param page: 페이지 수
        :param limit: 개수 제한 (default: 100, max: 100)
        :param order_by: 정렬 방식
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.get_withdraws(currency='XRP', state='DONE')
            print(res.json())

            [{
                "type": "withdraw",
                "uuid": "35a4f1dc-1db5-4d6b-89b5-7ec137875956",
                "currency": "XRP",
                "net_type": "XRP",
                "txid": "98c15999f0bdc4ae0e8a-ed35868bb0c204fe6ec29e4058a3451e-88636d1040f4baddf943274ce37cf9cc",
                "state": "DONE",
                "created_at": "2019-02-28T15:17:51+09:00",
                "done_at": "2019-02-28T15:22:12+09:00",
                "amount": "1.00",
                "fee": "0.0",
                "transaction_type": "default"
            }, ...]
        """
        url = self._endpoint + "/withdraws"
        params = {
            "currency": currency,
            "state": state,
            "uuids[]": uuids,
            "txids[]": txids,
            "page": page,
            "limit": limit,
            "order_by": order_by,
        }
        headers = self._get_request_headers(params, headers=kwargs.pop('headers', None))

        return self._request('get', url, headers=headers, params=params, **kwargs)

    def get_withdraw(self,
                     *,
                     uuid: Optional[str] = None,
                     txid: Optional[str] = None,
                     currency: Optional[str] = None,
                     **kwargs) -> Response:
        """개별 출금 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EA%B0%9C%EB%B3%84-%EC%B6%9C%EA%B8%88-%EC%A1%B0%ED%9A%8C>`_

        :param uuid: 출금 UUID
        :param txid: 출금 TXID
        :param currency: Currency 코드
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.get_withdraw(uuid='9f432943-54e0-40b7-825f-b6fec8b42b79')
            print(res.json())

            {
                "type": "withdraw",
                "uuid": "9f432943-54e0-40b7-825f-b6fec8b42b79",
                "currency": "BTC",
                "net_type": "BTC",
                "txid": null,
                "state": "processing",
                "created_at": "2018-04-13T11:24:01+09:00",
                "done_at": null,
                "amount": "0.01",
                "fee": "0.0",
                "transaction_type": "default"
            }
        """
        url = self._endpoint + "/withdraw"
        params = {
            "uuid": uuid,
            "txid": txid,
            "currency": currency,
        }
        headers = self._get_request_headers(params, headers=kwargs.pop('headers', None))

        return self._request('get', url, headers=headers, params=params, **kwargs)

    def get_withdraw_chance(self,
                            currency: str,
                            *,
                            net_type: str,
                            **kwargs) -> Response:
        """출금 가능 정보 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EC%B6%9C%EA%B8%88-%EA%B0%80%EB%8A%A5-%EC%A0%95%EB%B3%B4>`_

        :param currency: Currency 코드
        :param net_type: 출금 네트워크
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.get_withdraw_chance('BTC', net_type='BTC')
            print(res.json())

            {
                "member_level": {
                    "security_level": 3,
                    "fee_level": 0,
                    "email_verified": true,
                    "identity_auth_verified": true,
                    "bank_account_verified": true,
                    "two_factor_auth_verified": true,
                    "locked": false,
                    "wallet_locked": false
                },
                "currency": {
                    "code": "BTC",
                    "withdraw_fee": "0.0005",
                    "is_coin": true,
                    "wallet_state": "working",
                    "wallet_support": [
                      "deposit",
                      "withdraw"
                    ]
                },
                "account": {
                    "currency": "BTC",
                    "balance": "10.0",
                    "locked": "0.0",
                    "avg_buy_price": "8042000",
                    "avg_buy_price_modified": false,
                    "unit_currency": "KRW",
                },
                "withdraw_limit": {
                    "currency": "BTC",
                    "minimum": "0.001",
                    "onetime": null,
                    "daily": "10.0",
                    "remaining_daily": "10.0",
                    "remaining_daily_krw": "0.0",
                    "remaining_daily_fiat": "0.0",
                    "fiat_currency": "KRW",
                    "withdraw_delayed_fiat": "0.0",
                    "fixed": 8,
                    "can_withdraw": true,
                }
            }
        """
        url = self._endpoint + "/withdraws/chance"
        params = {
            "currency": currency,
            "net_type": net_type,
        }
        headers = self._get_request_headers(params, headers=kwargs.pop('headers', None))

        return self._request('get', url, headers=headers, params=params, **kwargs)

    def create_withdraw_coin(self,
                             currency: str,
                             *,
                             net_type: str,
                             amount: str,
                             address: str,
                             secondary_address: Optional[str] = None,
                             transaction_type: TransactionType = 'default',
                             **kwargs) -> Response:
        """디지털 자산 출금하기

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EC%BD%94%EC%9D%B8-%EC%B6%9C%EA%B8%88%ED%95%98%EA%B8%B0>`_

        :param currency: Currency 코드
        :param net_type: 출금 네트워크
        :param amount: 출금 수량
        :param address: 출금 가능 주소에 등록된 출금 주소
        :param secondary_address: 2차 출금 주소 (필요한 코인에 한해서)
        :param transaction_type: 출금 유형. default: 일반출금, internal: 바로출금
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.create_withdraw_coin('BTC', net_type='BTC', amount='0.01', address='1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa')
            print(res.json())

            {
                "type": "withdraw",
                "uuid": "9f432943-54e0-40b7-825f-b6fec8b42b79",
                "currency": "BTC",
                "net_type": "BTC",
                "txid": "ebe6937b-130e-4066-8ac6-4b0e67f28adc",
                "state": "processing",
                "created_at": "2018-04-13T11:24:01+09:00",
                "done_at": null,
                "amount": "0.01",
                "fee": "0.0",
                "krw_amount": "80420.0",
                "transaction_type": "default"
            }
        """
        url = self._endpoint + "/withdraws/coin"
        params = {
            "currency": currency,
            "net_type": net_type,
            "amount": amount,
            "address": address,
            "secondary_address": secondary_address,
            "transaction_type": transaction_type,
        }
        headers = self._get_request_headers(params, headers=kwargs.pop('headers', None))

        return self._request('post', url, headers=headers, json=params, **kwargs)

    def create_withdraw_krw(self,
                            amount: str,
                            *,
                            two_factor_type: TwoFactorType,
                            **kwargs) -> Response:
        """원화 출금하기

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EC%9B%90%ED%99%94-%EC%B6%9C%EA%B8%88%ED%95%98%EA%B8%B0>`_

        :param amount: 출금액
        :param two_factor_type: 2차 인증 수단
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.create_withdraw_krw('10000')
            print(res.json())

            {
                "type": "withdraw",
                "uuid": "9f432943-54e0-40b7-825f-b6fec8b42b79",
                "currency": "KRW",
                "txid": "ebe6937b-130e-4066-8ac6-4b0e67f28adc",
                "state": "processing",
                "created_at": "2018-04-13T11:24:01+09:00",
                "done_at": null,
                "amount": "10000",
                "fee": "0.0",
                "transaction_type": "default"
            }
        """
        url = self._endpoint + "/withdraws/krw"
        params = {
            "amount": amount,
            "two_factor_type": two_factor_type,
        }
        headers = self._get_request_headers(params, headers=kwargs.pop('headers', None))

        return self._request('post', url, headers=headers, json=params, **kwargs)

    def get_withdraw_addresses(self,
                               **kwargs) -> Response:
        """출금 허용 주소 리스트 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EC%B6%9C%EA%B8%88%ED%97%88%EC%9A%A9%EC%A3%BC%EC%86%8C-%EB%A6%AC%EC%8A%A4%ED%8A%B8-%EC%A1%B0%ED%9A%8C>`_

        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.get_withdraw_addresses()
            print(res.json())

            [{
                "currency": "BTC",
                "net_type": "BTC",
                "network_name": "Bitcoin",
                "withdraw_address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
                "secondary_address": null
            }, ...]
        """
        url = self._endpoint + "/withdraws/coin_addresses"
        headers = self._get_request_headers(headers=kwargs.pop('headers', None))

        return self._request('get', url, headers=headers, **kwargs)

    # --------------------------------------------------------------------------
    # Exchange API > 입금
    # --------------------------------------------------------------------------

    def get_deposits(self,
                     *,
                     currency: Optional[str] = None,
                     state: Optional[DepositState] = None,
                     uuids: Optional[List[str]] = None,
                     txids: Optional[List[str]] = None,
                     page: int = 1,
                     limit: int = 100,
                     order_by: OrderBy = 'desc',
                     **kwargs) -> Response:
        """입금 리스트 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EC%9E%85%EA%B8%88-%EB%A6%AC%EC%8A%A4%ED%8A%B8-%EC%A1%B0%ED%9A%8C>`_

        :param currency: Currency 코드
        :param state: 입금 상태
        :param uuids: 입금 UUID 리스트
        :param txids: 입금 TXID 리스트
        :param page: 페이지 수
        :param limit: 개수 제한 (default: 100, max: 100)
        :param order_by: 정렬 방식
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.get_deposits(currency='KRW')
            print(res.json())

            [{
                "type": "deposit",
                "uuid": "94332e99-3a87-4a35-ad98-28b0c969f830",
                "currency": "KRW",
                "net_type": None,
                "txid": "9e37c537-6849-4c8b-a134-57313f5dfc5a",
                "state": "ACCEPTED",
                "created_at": "2017-12-08T15:38:02+09:00",
                "done_at": "2017-12-08T15:38:02+09:00",
                "amount": "100000.0",
                "fee": "0.0",
                "transaction_type": "default"
            }, ...]
        """
        url = self._endpoint + "/deposits"
        params = {
            "currency": currency,
            "state": state,
            "uuids[]": uuids,
            "txids[]": txids,
            "page": page,
            "limit": limit,
            "order_by": order_by,
        }
        headers = self._get_request_headers(params, headers=kwargs.pop('headers', None))

        return self._request('get', url, headers=headers, params=params, **kwargs)

    def get_deposit(self,
                    *,
                    uuid: Optional[str] = None,
                    txid: Optional[str] = None,
                    currency: Optional[str] = None,
                    **kwargs) -> Response:
        """개별 입금 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EA%B0%9C%EB%B3%84-%EC%9E%85%EA%B8%88-%EC%A1%B0%ED%9A%8C>`_

        :param uuid: 출금 UUID
        :param txid: 출금 TXID
        :param currency: Currency 코드
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.get_deposit(uuid='94332e99-3a87-4a35-ad98-28b0c969f830')
            print(res.json())

            {
                "type": "deposit",
                "uuid": "94332e99-3a87-4a35-ad98-28b0c969f830",
                "currency": "KRW",
                "net_type": None,
                "txid": "9e37c537-6849-4c8b-a134-57313f5dfc5a",
                "state": "ACCEPTED",
                "created_at": "2017-12-08T15:38:02+09:00",
                "done_at": "2017-12-08T15:38:02+09:00",
                "amount": "100000.0",
                "fee": "0.0",
                "transaction_type": "default"
            }
        """
        url = self._endpoint + "/deposit"
        params = {
            "uuid": uuid,
            "txid": txid,
            "currency": currency,
        }
        headers = self._get_request_headers(params, headers=kwargs.pop('headers', None))

        return self._request('get', url, headers=headers, params=params, **kwargs)

    def create_coin_address(self,
                            currency: str,
                            *,
                            net_type: str,
                            **kwargs) -> Response:
        """입금 주소 생성 요청

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EC%9E%85%EA%B8%88-%EC%A3%BC%EC%86%8C-%EC%83%9D%EC%84%B1-%EC%9A%94%EC%B2%AD>`_

        :param currency: Currency 코드
        :param net_type: 입금 네트워크
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.create_coin_address('BTC', net_type='BTC')
            print(res.json())

            {
              "success": true,
              "message": "BTC 입금주소를 생성중입니다."
            }
        """
        url = self._endpoint + "/deposits/generate_coin_address"
        params = {
            "currency": currency,
            "net_type": net_type,
        }
        headers = self._get_request_headers(params, headers=kwargs.pop('headers', None))

        return self._request('post', url, headers=headers, json=params, **kwargs)

    def get_coin_addresses(self,
                           **kwargs) -> Response:
        """전체 입금 주소 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EC%A0%84%EC%B2%B4-%EC%9E%85%EA%B8%88-%EC%A3%BC%EC%86%8C-%EC%A1%B0%ED%9A%8C>`_

        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.get_coin_addresses()
            print(res.json())

            [{
                "currency": "BTC",
                "net_type": "BTC",
                "deposit_address": "3EusRwybuZUhVDeHL7gh3HSLmbhLcy7NqD",
                "secondary_address": null
            }, ...]
        """
        url = self._endpoint + "/deposits/coin_addresses"
        headers = self._get_request_headers(headers=kwargs.pop('headers', None))

        return self._request('get', url, headers=headers, **kwargs)

    def get_coin_address(self,
                         currency: str,
                         *,
                         net_type: str,
                         **kwargs) -> Response:
        """개별 입금 주소 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EA%B0%9C%EB%B3%84-%EC%9E%85%EA%B8%88-%EC%A3%BC%EC%86%8C-%EC%A1%B0%ED%9A%8C>`_

        :param currency: Currency 코드
        :param net_type: 입금 네트워크
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.get_coin_address('BTC', net_type='BTC')
            print(res.json())

            {
                "currency": "BTC",
                "net_type": "BTC",
                "deposit_address": "3EusRwybuZUhVDeHL7gh3HSLmbhLcy7NqD",
                "secondary_address": null
            }
        """
        url = self._endpoint + "/deposits/coin_address"
        params = {
            "currency": currency,
            "net_type": net_type,
        }
        headers = self._get_request_headers(params, headers=kwargs.pop('headers', None))

        return self._request('get', url, headers=headers, params=params, **kwargs)

    def create_deposit_krw(self,
                           amount: str,
                           *,
                           two_factor_type: TwoFactorType,
                           **kwargs) -> Response:
        """원화 입금하기

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EC%9B%90%ED%99%94-%EC%9E%85%EA%B8%88%ED%95%98%EA%B8%B0>`_

        :param amount: 입금액
        :param two_factor_type: 2차 인증 수단
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.create_deposit_krw('10000')
            print(res.json())

            {
                "type": "deposit",
                "uuid": "9f432943-54e0-40b7-825f-b6fec8b42b79",
                "currency": "KRW",
                "txid": "ebe6937b-130e-4066-8ac6-4b0e67f28adc",
                "state": "processing",
                "created_at": "2018-04-13T11:24:01+09:00",
                "done_at": null,
                "amount": "10000",
                "fee": "0.0",
                "transaction_type": "default"
            }
        """
        url = self._endpoint + "/deposits/krw"
        params = {
            "amount": amount,
            "two_factor_type": two_factor_type,
        }
        headers = self._get_request_headers(params, headers=kwargs.pop('headers', None))

        return self._request('post', url, headers=headers, json=params, **kwargs)

    def get_vasps(self, **kwargs) -> Response:
        """계정주 확인(트래블룰 검증)가능 거래소 리스트 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%ED%8A%B8%EB%9E%98%EB%B8%94%EB%A3%B0-%EA%B0%80%EB%8A%A5-%EA%B1%B0%EB%9E%98%EC%86%8C>`_

        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.get_vasps()
            print(res.json())

            [{
              "vasp_name": "업비트 인도네시아",
              "vasp_uuid": "00000000-0000-0000-0000-000000000000",
              "depositable": True,
              "withdrawable": True
            }, ...]
        """
        url = self._endpoint + "/travel_rule/vasps"
        headers = self._get_request_headers(headers=kwargs.pop('headers', None))

        return self._request('get', url, headers=headers, **kwargs)

    def verify_travel_rule_by_uuid(self, *,
                                   vasp_uuid: str,
                                   deposit_uuid: str,
                                   **kwargs) -> Response:
        """입금 UUID로 트래블룰 검증하기

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%ED%8A%B8%EB%9E%98%EB%B8%94%EB%A3%B0-uuid>`_

        :param vasp_uuid: 상대 거래소 UUID
        :param deposit_uuid: 입금 UUID
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.verify_travel_rule_by_uuid(deposit_uuid='xxx', vasp_uuid='xxx')
            print(res.json())

            {
              "deposit_uuid": "00000000-0000-0000-0000-000000000000",
              "verification_result": "verified",
              "deposit_state": "PROCESSING"
            }
        """
        url = self._endpoint + "/travel_rule/deposit/uuid"
        params = {
            "vasp_uuid": vasp_uuid,
            "deposit_uuid": deposit_uuid,
        }
        headers = self._get_request_headers(params, headers=kwargs.pop('headers', None))

        return self._request('post', url, headers=headers, json=params, **kwargs)

    def verify_travel_rule_by_txid(self, *,
                                   vasp_uuid: str,
                                   txid: str,
                                   currency: str,
                                   net_type: str,
                                   **kwargs) -> Response:
        """입금 TxID로 트래블룰 검증하기

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%ED%8A%B8%EB%9E%98%EB%B8%94%EB%A3%B0-txid>`_

        :param vasp_uuid: 상대 거래소 UUID
        :param txid: 입금 TxID
        :param currency: 입금 화폐
        :param net_type: 입금 네트워크 타입
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.verify_travel_rule_by_txid(deposit_uuid='xxx', vasp_uuid='xxx')
            print(res.json())

            {
              "deposit_uuid": "00000000-0000-0000-0000-000000000000",
              "verification_result": "verified",
              "deposit_state": "PROCESSING"
            }
        """
        url = self._endpoint + "/travel_rule/deposit/txid"
        params = {
            "vasp_uuid": vasp_uuid,
            "txid": txid,
            "currency": currency,
            "net_type": net_type,
        }
        headers = self._get_request_headers(params, headers=kwargs.pop('headers', None))

        return self._request('post', url, headers=headers, json=params, **kwargs)

    # --------------------------------------------------------------------------
    # Exchange API > 서비스 정보
    # --------------------------------------------------------------------------

    def get_wallet_status(self,
                          **kwargs) -> Response:
        """입출금 현황 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EC%9E%85%EC%B6%9C%EA%B8%88-%ED%98%84%ED%99%A9>`_

        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.get_wallet_status()
            print(res.json())

            [{
                'currency': 'BTC',
                'net_type': 'BTC',
                'wallet_state': 'working',
                'block_state': 'normal',
                'block_height': 776512,
                'block_updated_at': '2023-02-14T13:37:39.806+00:00',
                'block_elapsed_minutes': 12
            }, ...]
        """
        url = self._endpoint + "/status/wallet"
        headers = self._get_request_headers(headers=kwargs.pop('headers', None))

        return self._request('get', url, headers=headers, **kwargs)

    def get_api_keys(self,
                     **kwargs) -> Response:
        """API 키 리스트 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/open-api-%ED%82%A4-%EB%A6%AC%EC%8A%A4%ED%8A%B8-%EC%A1%B0%ED%9A%8C>`_

        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :raises upbit.exceptions.ApiKeyError: 인증 정보 없이 호출시 발생.

        :return: API 서버 응답

        Usage::

            access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
            secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
            upbit = Upbit(access_key, secret_key)
            res = upbit.get_api_keys()
            print(res.json())

            [{
                'access_key': 'xxxxxxxxxxxxxxxxxxxxxxxx',
                'expire_at': '2021-03-09T12:39:39+00:00'
             }, ...]
        """
        url = self._endpoint + "/api_keys"
        headers = self._get_request_headers(headers=kwargs.pop('headers', None))

        return self._request('get', url, headers=headers, **kwargs)

    # --------------------------------------------------------------------------
    # Quotation API > 시세 종목 조회
    # --------------------------------------------------------------------------

    def get_markets(self,
                    is_detail: bool = False,
                    **kwargs) -> Response:
        """마켓 코드 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EB%A7%88%EC%BC%93-%EC%BD%94%EB%93%9C-%EC%A1%B0%ED%9A%8C>`_

        :param is_detail: 유의종목 필드과 같은 상세 정보 노출 여부
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :return: API 서버 응답

        Usage::

            upbit = Upbit()
            res = upbit.get_markets(True)
            print(res.json())

            [{
                "market": "KRW-BTC",
                "korean_name": "비트코인",
                "english_name": "Bitcoin",
                "market_warning": "NONE",
                "market_event": {
                  "warning": false,
                  "caution": {
                    "PRICE_FLUCTUATIONS": false,
                    "TRADING_VOLUME_SOARING": false,
                    "DEPOSIT_AMOUNT_SOARING": true,
                    "GLOBAL_PRICE_DIFFERENCES": false,
                    "CONCENTRATION_OF_SMALL_ACCOUNTS": false
                  }
            }, ...]
        """
        url = self._endpoint + "/market/all"
        params = {
            "is_details": is_detail,
        }

        return self._request('get', url, params=params, **kwargs)

    # --------------------------------------------------------------------------
    # Quotation API > 시세 캔들 조회
    # --------------------------------------------------------------------------

    def get_candles_minute(self,
                           unit: MinuteUnit,
                           market: str,
                           *,
                           to: Optional[str] = None,
                           count: Optional[int] = None,
                           **kwargs) -> Response:
        """분(Minute) 캔들 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EB%B6%84minute-%EC%BA%94%EB%93%A4-1>`_

        :param unit: 분 단위.
        :param market: 마켓 코드 (ex. KRW-BTC)
        :param to: 마지막 캔들 시각 (exclusive). 포맷 : yyyy-MM-dd'T'HH:mm:ss'Z' or yyyy-MM-dd HH:mm:ss. 비워서 요청시 가장 최근 캔들
        :param count: 캔들 개수. 최대 200
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :return: API 서버 응답

        Usage::

            upbit = Upbit()
            res = upbit.get_candles_minute(1, 'KRW-BTC')
            print(res.json())

            [{
                'market': 'KRW-BTC',
                'candle_date_time_utc': '2023-02-14T09:43:00',
                'candle_date_time_kst': '2023-02-14T18:43:00',
                'opening_price': 28087000.0,
                'high_price': 28090000.0,
                'low_price': 28080000.0,
                'trade_price': 28090000.0,
                'timestamp': 1676367808940,
                'candle_acc_trade_price': 71066390.72097,
                'candle_acc_trade_volume': 2.53044043,
                'unit': 1
            }, ...]
        """
        url = self._endpoint + "/candles/minutes/" + str(unit)
        params = {
            "market": market,
            "to": to,
            "count": count,
        }

        return self._request('get', url, params=params, **kwargs)

    def get_candles_second(self,
                           market: str,
                           *,
                           to: Optional[str] = None,
                           count: Optional[int] = None,
                           **kwargs) -> Response:
        """초(Second) 캔들 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EC%B4%88second-%EC%BA%94%EB%93%A4>`_

        :param market: 마켓 코드 (ex. KRW-BTC)
        :param to: 마지막 캔들 시각 (exclusive). 포맷 : yyyy-MM-dd'T'HH:mm:ss'Z' or yyyy-MM-dd HH:mm:ss. 비워서 요청시 가장 최근 캔들
        :param count: 캔들 개수. 최대 200
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :return: API 서버 응답

        Usage::

            upbit = Upbit()
            res = upbit.get_candles_second('KRW-BTC')
            print(res.json())

            [{
                "market": "KRW-BTC",
                "candle_date_time_utc": "2024-07-30T09:32:41",
                "candle_date_time_kst": "2024-07-30T18:32:41",
                "opening_price": 93557000,
                "high_price": 93557000,
                "low_price": 93551000,
                "trade_price": 93551000,
                "timestamp": 1722331961297,
                "candle_acc_trade_price": 485957.73742,
                "candle_acc_trade_volume": 0.0051944
            }, ...]
        """
        url = self._endpoint + "/candles/seconds"
        params = {
            "market": market,
            "to": to,
            "count": count,
        }

        return self._request('get', url, params=params, **kwargs)

    def get_candles_day(self,
                        market: str,
                        *,
                        to: Optional[str] = None,
                        count: Optional[int] = None,
                        converting_price_unit: Optional[str] = None,
                        **kwargs) -> Response:
        """일(Day) 캔들 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EC%9D%BCday-%EC%BA%94%EB%93%A4-1>`_

        :param market: 마켓 코드 (ex. KRW-BTC)
        :param to: 마지막 캔들 시각 (exclusive). 포맷 : yyyy-MM-dd'T'HH:mm:ss'Z' or yyyy-MM-dd HH:mm:ss. 비워서 요청시 가장 최근 캔들
        :param count: 캔들 개수. 최대 200
        :param converting_price_unit: 원화 마켓이 아닌 다른 마켓(ex. BTC, USDT)의 일봉 요청시, 종가 환산 화폐 단위 (예, KRW)
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :return: API 서버 응답

        Usage::

            upbit = Upbit()
            res = upbit.get_candles_day('USDT-BTC', converting_price_unit='KRW')
            print(res.json())

            [{
                'market': 'USDT-BTC',
                'candle_date_time_utc': '2023-02-14T00:00:00',
                'candle_date_time_kst': '2023-02-14T09:00:00',
                'opening_price': 21366.66292861,
                'high_price': 21977.99979999,
                'low_price': 21121.0004,
                'trade_price': 21873.26751835,
                'timestamp': 1676368771710,
                'candle_acc_trade_price': 147537.66926034,
                'candle_acc_trade_volume': 6.80355829,
                'prev_closing_price': 21366.46782971,
                'change_price': 506.79968864,
                'change_rate': 0.0237193949,
                'converted_trade_price': 28139000.000001043
            }, ...]
        """
        url = self._endpoint + "/candles/days"
        params = {
            "market": market,
            "to": to,
            "count": count,
            "converting_price_unit": converting_price_unit,
        }

        return self._request('get', url, params=params, **kwargs)

    def get_candles_week(self,
                         market: str,
                         *,
                         to: Optional[str] = None,
                         count: Optional[int] = None,
                         **kwargs) -> Response:
        """주(Week) 캔들 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EC%A3%BCweek-%EC%BA%94%EB%93%A4-1>`_

        :param market: 마켓 코드 (ex. KRW-BTC)
        :param to: 마지막 캔들 시각 (exclusive). 포맷 : yyyy-MM-dd'T'HH:mm:ss'Z' or yyyy-MM-dd HH:mm:ss. 비워서 요청시 가장 최근 캔들
        :param count: 캔들 개수. 최대 200
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :return: API 서버 응답

        Usage::

            upbit = Upbit()
            res = upbit.get_candles_week('KRW-BTC')
            print(res.json())

            [{
                'market': 'KRW-BTC',
                'candle_date_time_utc': '2023-02-14T09:43:00',
                'candle_date_time_kst': '2023-02-14T18:43:00',
                'opening_price': 28087000.0,
                'high_price': 28090000.0,
                'low_price': 28080000.0,
                'trade_price': 28090000.0,
                'timestamp': 1676367808940,
                'candle_acc_trade_price': 71066390.72097,
                'candle_acc_trade_volume': 2.53044043,
                'first_day_of_period': '2023-02-13'
            }, ...]
        """
        url = self._endpoint + "/candles/weeks"
        params = {
            "market": market,
            "to": to,
            "count": count,
        }

        return self._request('get', url, params=params, **kwargs)

    def get_candles_month(self,
                          market: str,
                          *,
                          to: Optional[str] = None,
                          count: Optional[int] = None,
                          **kwargs) -> Response:
        """월(Month) 캔들 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EC%9B%94month-%EC%BA%94%EB%93%A4-1>`_

        :param market: 마켓 코드 (ex. KRW-BTC)
        :param to: 마지막 캔들 시각 (exclusive). 포맷 : yyyy-MM-dd'T'HH:mm:ss'Z' or yyyy-MM-dd HH:mm:ss. 비워서 요청시 가장 최근 캔들
        :param count: 캔들 개수. 최대 200
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :return: API 서버 응답

        Usage::

            upbit = Upbit()
            res = upbit.get_candles_month('KRW-BTC')
            print(res.json())

            [{
                'market': 'KRW-BTC',
                'candle_date_time_utc': '2023-02-14T09:43:00',
                'candle_date_time_kst': '2023-02-14T18:43:00',
                'opening_price': 28087000.0,
                'high_price': 28090000.0,
                'low_price': 28080000.0,
                'trade_price': 28090000.0,
                'timestamp': 1676367808940,
                'candle_acc_trade_price': 71066390.72097,
                'candle_acc_trade_volume': 2.53044043,
                'first_day_of_period': '2023-02-01'
            }, ...]
        """
        url = self._endpoint + "/candles/months"
        params = {
            "market": market,
            "to": to,
            "count": count,
        }

        return self._request('get', url, params=params, **kwargs)

    def get_candles_year(self,
                         market: str,
                         *,
                         to: Optional[str] = None,
                         count: Optional[int] = None,
                         **kwargs) -> Response:
        """연(Year) 캔들 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/kr/reference/%EB%85%84year-%EC%BA%94%EB%93%A4>`_

        :param market: 마켓 코드 (ex. KRW-BTC)
        :param to: 마지막 캔들 시각 (exclusive). 포맷 : yyyy-MM-dd'T'HH:mm:ss'Z' or yyyy-MM-dd HH:mm:ss. 비워서 요청시 가장 최근 캔들
        :param count: 캔들 개수. 최대 200
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :return: API 서버 응답

        Usage::

            upbit = Upbit()
            res = upbit.get_candles_year('KRW-BTC')
            print(res.json())

            [{
                "market": "KRW-BTC",
                "candle_date_time_utc": "2024-01-01T00:00:00",
                "candle_date_time_kst": "2024-01-01T09:00:00",
                "opening_price": 96290000,
                "high_price": 1231356000,
                "low_price": 124.5,
                "trade_price": 85375000,
                "timestamp": 1727845502277,
                "candle_acc_trade_price": 60613272545.65653,
                "candle_acc_trade_volume": 708.81714523,
                "first_day_of_period": "2024-01-01"
            }, ...]
        """
        url = self._endpoint + "/candles/years"
        params = {
            "market": market,
            "to": to,
            "count": count,
        }

        return self._request('get', url, params=params, **kwargs)

    # --------------------------------------------------------------------------
    # Quotation API > 시세 체결 조회
    # --------------------------------------------------------------------------

    def get_trades_ticks(self,
                         market: str,
                         *,
                         to: Optional[str] = None,
                         count: Optional[int] = None,
                         cursor: Optional[str] = None,
                         days_ago: Optional[Literal[1, 2, 3, 4, 5, 6, 7]] = None,
                         **kwargs) -> Response:
        """최근 체결 내역 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%EC%B5%9C%EA%B7%BC-%EC%B2%B4%EA%B2%B0-%EB%82%B4%EC%97%AD>`_

        :param market: 마켓 코드 (ex. KRW-BTC)
        :param to: 마지막 체결 시각. 형식 : [HHmmss 또는 HH:mm:ss]. 비워서 요청시 가장 최근 데이터
        :param count: 체결 개수. 최대 500개
        :param cursor: 페이지네이션 커서 (sequentialId)
        :param days_ago: 최근 체결 날짜 기준 7일 이내의 이전 데이터 조회 가능. 비워서 요청 시 가장 최근 체결 날짜 반환. 범위: 1~7
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :return: API 서버 응답

        Usage::

            upbit = Upbit()
            res = upbit.get_trades_ticks('KRW-BTC')
            print(res.json())

            [{
                'market': 'KRW-BTC',
                'trade_date_utc': '2023-02-14',
                'trade_time_utc': '12:52:42',
                'timestamp': 1676379162028,
                'trade_price': 28250000.0,
                'trade_volume': 0.00353982,
                'prev_closing_price': 28309000.0,
                'change_price': -59000.0,
                'ask_bid': 'BID',
                'sequential_id': 1676379162028000
            }, ...]
        """
        url = self._endpoint + "/trades/ticks"
        params = {
            "market": market,
            "to": to,
            "count": count,
            "cursor": cursor,
            "days_ago": days_ago,
        }

        return self._request('get', url, params=params, **kwargs)

    # --------------------------------------------------------------------------
    # Quotation API > 시세 현재가 조회
    # --------------------------------------------------------------------------

    def get_ticker(self,
                   markets: List[str],
                   **kwargs) -> Response:
        """현재가 정보 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/ticker%ED%98%84%EC%9E%AC%EA%B0%80-%EC%A0%95%EB%B3%B4>`_

        :param markets: 마켓 코드 리스트 (ex. ["KRW-BTC"])
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :return: API 서버 응답

        Usage::

            upbit = Upbit()
            res = upbit.get_ticker(['KRW-BTC'])
            print(res.json())

            [{
                'market': 'KRW-BTC',
                'trade_date': '20230214',
                'trade_time': '130155',
                'trade_date_kst': '20230214',
                'trade_time_kst': '220155',
                'trade_timestamp': 1676379715095,
                'opening_price': 28334000,
                'high_price': 28344000,
                'low_price': 28055000,
                'trade_price': 28256000,
                'prev_closing_price': 28309000.0,
                'change': 'FALL',
                'change_price': 53000.0,
                'change_rate': 0.0018721961,
                'signed_change_price': -53000.0,
                'signed_change_rate': -0.0018721961,
                'trade_volume': 0.01116417,
                'acc_trade_price': 101147638956.17886,
                'acc_trade_price_24h': 136755693662.07787,
                'acc_trade_volume': 3589.8072519,
                'acc_trade_volume_24h': 4856.21610445,
                'highest_52_week_price': 57678000.0,
                'highest_52_week_date': '2022-03-28',
                'lowest_52_week_price': 20700000.0,
                'lowest_52_week_date': '2022-12-30',
                'timestamp': 1676379715138
            }, ...]
        """
        url = self._endpoint + "/ticker"
        params = {
            "markets": markets,
        }

        return self._request('get', url, params=params, **kwargs)

    def get_tickers_by_quote(self,
                             quotes: List[str],
                             **kwargs) -> Response:
        """마켓 단위 현재가 정보 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/tickers_by_quote>`_

        :param quotes: 거래 화폐 코드 리스트 (ex. ["KRW", "BTC", "USDT"])
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :return: API 서버 응답

        Usage::

            upbit = Upbit()
            res = upbit.get_tickers_by_quote(['KRW'])
            print(res.json())

            [{
                'market': 'KRW-BTC',
                'trade_date': '20230214',
                'trade_time': '130155',
                'trade_date_kst': '20230214',
                'trade_time_kst': '220155',
                'trade_timestamp': 1676379715095,
                'opening_price': 28334000,
                'high_price': 28344000,
                'low_price': 28055000,
                'trade_price': 28256000,
                'prev_closing_price': 28309000.0,
                'change': 'FALL',
                'change_price': 53000.0,
                'change_rate': 0.0018721961,
                'signed_change_price': -53000.0,
                'signed_change_rate': -0.0018721961,
                'trade_volume': 0.01116417,
                'acc_trade_price': 101147638956.17886,
                'acc_trade_price_24h': 136755693662.07787,
                'acc_trade_volume': 3589.8072519,
                'acc_trade_volume_24h': 4856.21610445,
                'highest_52_week_price': 57678000.0,
                'highest_52_week_date': '2022-03-28',
                'lowest_52_week_price': 20700000.0,
                'lowest_52_week_date': '2022-12-30',
                'timestamp': 1676379715138
            }, ...]
        """
        url = self._endpoint + "/ticker/all"
        params = {
            "quote_currencies": quotes,
        }

        return self._request('get', url, params=params, **kwargs)

    # --------------------------------------------------------------------------
    # Quotation API > 시세 호가 조회
    # --------------------------------------------------------------------------

    def get_orderbook(self,
                      markets: List[str],
                      *,
                      level: float = None,
                      **kwargs) -> Response:
        """호가 정보 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/%ED%98%B8%EA%B0%80-%EC%A0%95%EB%B3%B4-%EC%A1%B0%ED%9A%8C>`_

        :param markets: 마켓 코드 리스트 (ex. ["KRW-BTC"])
        :param level: 호가 모아보기 단위 (0인 경우 기본 호가 단위. 해당 기능은 원화마켓(KRW)에서만 지원)
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :return: API 서버 응답

        Usage::

            upbit = Upbit()
            res = upbit.get_orderbook(['KRW-BTC'])
            print(res.json())

            [{
                'market': 'KRW-BTC',
                'timestamp': 1676380537532,
                'total_ask_size': 5.71529774,
                'total_bid_size': 3.5650408600000008,
                'level': 0,
                'orderbook_units':
                    [{'ask_price': 28252000.0, 'bid_price': 28242000.0, 'ask_size': 0.22130992, 'bid_size': 0.69372092},
                    {'ask_price': 28253000.0, 'bid_price': 28241000.0, 'ask_size': 0.51485752, 'bid_size': 0.01781927},
                    {'ask_price': 28254000.0, 'bid_price': 28240000.0, 'ask_size': 1.23555378, 'bid_size': 0.93009378},
                    {'ask_price': 28255000.0, 'bid_price': 28239000.0, 'ask_size': 0.00473407, 'bid_size': 0.22},
                    {'ask_price': 28259000.0, 'bid_price': 28237000.0, 'ask_size': 0.49577839, 'bid_size': 0.00067571},
                    {'ask_price': 28261000.0, 'bid_price': 28233000.0, 'ask_size': 0.69107286, 'bid_size': 0.04437211},
                    {'ask_price': 28264000.0, 'bid_price': 28232000.0, 'ask_size': 0.01106274, 'bid_size': 0.18722972},
                    {'ask_price': 28265000.0, 'bid_price': 28231000.0, 'ask_size': 0.46430584, 'bid_size': 1.2079},
                    {'ask_price': 28266000.0, 'bid_price': 28230000.0, 'ask_size': 0.01860825, 'bid_size': 0.00318532},
                    {'ask_price': 28267000.0, 'bid_price': 28228000.0, 'ask_size': 0.02096061, 'bid_size': 0.01687993},
                    {'ask_price': 28268000.0, 'bid_price': 28227000.0, 'ask_size': 0.01, 'bid_size': 0.02220865},
                    {'ask_price': 28269000.0, 'bid_price': 28225000.0, 'ask_size': 0.0169, 'bid_size': 0.00035429},
                    {'ask_price': 28270000.0, 'bid_price': 28223000.0, 'ask_size': 0.02017691, 'bid_size': 0.02408774},
                    {'ask_price': 28271000.0, 'bid_price': 28222000.0, 'ask_size': 0.17979996, 'bid_size': 0.08573207},
                    {'ask_price': 28272000.0, 'bid_price': 28221000.0, 'ask_size': 1.81017689, 'bid_size': 0.11078135}
            }, ...]
        """
        url = self._endpoint + "/orderbook"
        params = {
            "markets": markets,
            "level": level,
        }

        return self._request('get', url, params=params, **kwargs)

    @deprecated("Use get_orderbook_instruments method instead.")
    def get_orderbook_levels(self,
                             markets: List[str],
                             **kwargs) -> Response:
        """호가 모아보기 단위 정보 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/reference/supported_levels>`_

        :param markets: 마켓 코드 리스트 (ex. ["KRW-BTC"])
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :return: API 서버 응답

        Usage::

            upbit = Upbit()
            res = upbit.get_orderbook_levels(['KRW-BTC'])
            print(res.json())

            [{
                "market": "KRW-BTC",
                "supported_levels": [
                    0,
                    10000,
                    100000,
                    1000000,
                    10000000
                ]
            }, ...]
        """
        url = self._endpoint + "/orderbook/supported_levels"
        params = {
            "markets": markets,
        }

        return self._request('get', url, params=params, **kwargs)

    def get_orderbook_instruments(self,
                                  markets: List[str],
                                  **kwargs) -> Response:
        """호가 정책 조회

        API 요청 및 응답에 대한 자세한 정보는 공식 문서 참고:
        `Upbit API Doc <https://docs.upbit.com/kr/reference/%ED%98%B8%EA%B0%80-%EC%A0%95%EC%B1%85-%EC%A1%B0%ED%9A%8C>`_

        :param markets: 마켓 코드 리스트 (ex. ["KRW-BTC"])
        :param kwargs: `requests.Session.request` 호출에 사용할 파라미터

        :return: API 서버 응답

        Usage::

            upbit = Upbit()
            res = upbit.get_orderbook_instruments(['KRW-BTC'])
            print(res.json())

            [{
                "market": "KRW-BTC",
                "quote_currency": "KRW",
                "tick_size": "1000",
                "supported_levels": [
                    "0",
                    "10000",
                    "100000",
                    "1000000",
                    "10000000",
                    "100000000"
                ]
            }, ...]
        """
        url = self._endpoint + "/orderbook/instruments"
        params = {
            "markets": markets,
        }

        return self._request('get', url, params=params, **kwargs)
