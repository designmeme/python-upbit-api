import datetime
import re
from typing import Literal

from .exceptions import InvalidRemainingReq

OrderBy = Literal['asc', 'desc']
"""데이터 정렬 방식

- asc: 오름차순
- desc: 내림차순
"""

OpenOrderState = Literal['wait', 'watch']
ClosedOrderState = Literal['done', 'cancel']
OrderState = Literal['wait', 'watch', 'done', 'cancel']
"""주문 상태

- wait: 체결 대기
- watch: 예약주문 대기
- done: 전체 체결 완료
- cancel: 주문 취소
"""

OrderSide = Literal['bid', 'ask']
"""주문 종류

- bid: 매수
- ask: 매도
"""

OrderType = Literal['limit', 'price', 'market']
"""주문 타입

- limit: 지정가 주문
- price: 시장가 주문(매수)
- market: 시장가 주문(매도)
"""

WithdrawState = Literal['WAITING', 'PROCESSING', 'DONE', 'FAILED', 'CANCELLED', 'REJECTED']
"""출금 상태

- WAITING: 대기중
- PROCESSING: 진행중
- DONE: 완료
- FAILED: 실패
- CANCELLED: 취소됨
- REJECTED: 거절됨
"""

DepositState = Literal['PROCESSING', 'ACCEPTED', 'CANCELLED', 'REJECTED', 'TRAVEL_RULE_SUSPECTED', 'REFUNDING', 'REFUNDED']
"""입금 상태

- PROCESSING: 진행중
- ACCEPTED: 완료
- CANCELLED: 취소됨
- REJECTED: 거절됨
- TRAVEL_RULE_SUSPECTED: 트래블룰 추가 인증 대기중
- REFUNDING: 반환절차 진행중
- REFUNDED: 반환됨
"""

TransactionType = Literal['default', 'internal']
"""입출금 유형

- default: 일반
- internal: 바로
"""

TwoFactorType = Literal['kakao', 'naver', 'hana']
"""2차 인증 수단

- kakao: 카카오 인증
- naver: 네이버 인증
- hana: 하나인증서 인증
"""

WalletState = Literal['working', 'withdraw_only', 'deposit_only', 'paused', 'unsupported']
"""입출금 상태

- working: 입출금 가능
- withdraw_only: 출금만 가능
- deposit_only: 입금만 가능
- paused: 입출금 중단
- unsupported: 입출금 미지원
"""

BlockState = Literal['normal', 'delayed', 'inactive']
"""블록 상태

- normal: 정상
- delayed: 지연
- inactive: 비활성 (점검 등)
"""

MarketWarningType = Literal['NONE', 'CAUTION']
"""유의 종목 여부

- NONE: 해당 사항 없음
- CAUTION: 투자유의
"""

MinuteUnit = Literal[1, 3, 5, 15, 10, 30, 60, 240]
"""분 캔들의 분 단위"""

RequestGroup = Literal[
    'default', 'order',
    'market', 'candles', 'ticker', 'crix-trades', 'orderbook',
]
"""잔여 요청 그룹

- default: Exchange API 주문 요청 외
- order: Exchange API 주문 요청
- market: Quotation API 시세 종목 조회
- candles: Quotation API 시세 캔들 조회
- crix-trades: Quotation API 시세 체결 조회
- ticker: Quotation API 시세 현재가 조회
- orderbook: Quotation API 시세 호가 정보 조회
"""


class RemainingReq:
    """
    잔여 요청수 클래스

    자세한 정보는 공식 문서 참고:
    `Upbit API Doc <https://docs.upbit.com/docs/user-request-guide>`_

    :param group: RequestGroup 잔여 요청 그룹명
    :param minute: 그룹별 분당 남은 요청수.
    :param second: 그룹별 초당 남은 요청수.
    :param updated: 요청수 응답을 저장한 일시. Deprecated. 삭제 예정.
    :param updated_at: 요청수 응답을 저장한 일시.
    """

    def __init__(self, remaining_req: str):
        """
        :param remaining_req: 응답 헤더 'Remaining-Req' 값
        """
        self._remaining_req = remaining_req

        pattern = re.compile(r"group=([a-z\-]+); min=([0-9]+); sec=([0-9]+)")
        matched = pattern.search(remaining_req)

        try:
            self.group: RequestGroup = matched.group(1)
            self.minute: int = int(matched.group(2))
            self.second: int = int(matched.group(3))
        except AttributeError:
            raise InvalidRemainingReq(f'Invalid Remaining Req {remaining_req=!r}')
        # todo delete: Deprecated. 삭제 예정.
        self.updated: datetime.datetime = datetime.datetime.now()
        self.updated_at: datetime.datetime = datetime.datetime.now(tz=datetime.timezone.utc)

    def __str__(self):
        return f"RemainingReq group={self.group!r}; min={self.minute!r}; sec={self.second!r}; updated_at={self.updated_at!r}"

    def __repr__(self):
        return f"RemainingReq(${self._remaining_req!r})"
