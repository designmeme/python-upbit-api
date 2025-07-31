# Python Upbit API

💙 Python Upbit API는 간단하고 명료한 Upbit API Wrapper 입니다. 👍

[![Version](https://img.shields.io/pypi/v/python-upbit-api)][pypi]
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/python-upbit-api)][pypi]
[![License](https://img.shields.io/pypi/l/python-upbit-api)][license]
[![PyPI Downloads](https://img.shields.io/pypi/dm/python-upbit-api)][downloads]


## Installation

pip 명령어로 간단하게 설치할 수 있습니다.

```shell
pip install python-upbit-api
```

## Quick Start

### 인증 없이 사용하기
각종 시세 정보를 얻기 위한 **QUOTATION API만** 사용한다면 인증 정보 없이 초기화 후 사용합니다.
<br/>⚠️ EXCHANGE API를 사용하면 `upbit.exceptions.ApiKeyError` 예외가 발생합니다.

```python
# example.py
from upbit import Upbit

upbit = Upbit()
res = upbit.get_markets()
data = res.json()

upbit.get_accounts() # upbit.exceptions.ApiKeyError 발생
```

### 인증 사용하기

인증이 필요한 **EXCHANGE API**를 사용해야 한다면 인증 정보를 초기화시 등록 후 사용합니다. 
<br/>🙆🏻‍♀️ QUOTATION API도 사용할 수 있습니다.

`.env` 환경설정 파일에 발급 받은 인증 정보를 설정합니다.
```
UPBIT_OPEN_API_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
UPBIT_OPEN_API_SECRET_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

```python
# example.py
import os
from upbit import Upbit

access_key = os.environ.get('UPBIT_OPEN_API_ACCESS_KEY')
secret_key = os.environ.get('UPBIT_OPEN_API_SECRET_KEY')
upbit = Upbit(access_key, secret_key)
res = upbit.get_accounts()
data = res.json()
```

## Features

### 업비트 REST API를 모두 메서드로 제공

[업비트 REST API][upbit docs api]를 `Upbit` 클래스의 메서드로 제공합니다.
자세한 내용은 [upbit.py](https://github.com/designmeme/python-upbit-api/blob/main/upbit/upbit.py) 파일 내 docstring 참조.

|    |                              | 메서드명                       |
|----|:-----------------------------|:---------------------------|
| 자산 | 전체 계좌 조회                     | get_accounts               |
| 주문 | 주문 가능 정보                     | get_order_chance           |
|  | 개별 주문 조회                     | get_order                  |
|  | 주문 리스트 조회                    | get_orders                 |
|  | id로 주문리스트 조회                 | get_orders_by_id           |
|  | 체결 대기 주문 (Open Order) 조회     | get_open_orders            |
|  | 종료된 주문 (Closed Order) 조회     | get_closed_orders          |
|  | 주문 취소 접수                     | delete_order               |
|  | 주문 일괄 취소 접수 | delete_orders |
|  | id로 주문리스트 취소 접수 | delete_orders_by_id |
|  | 주문하기                         | create_order               |
| 출금 | 출금 리스트 조회                    | get_withdraws              |
|  | 개별 출금 조회                     | get_withdraw               |
|  | 출금 가능 정보                     | get_withdraw_chance        |
|  | 디지털 자산 출금하기                  | create_withdraw_coin       |
|  | 원화 출금하기                      | create_withdraw_krw        |
|  | 출금 허용 주소 리스트 조회              | get_withdraw_addresses     |
| 입금 | 입금 리스트 조회                    | get_deposits               |
|  | 개별 입금 조회                     | get_deposit                |
|  | 입금 주소 생성 요청                  | create_coin_address        |
|  | 전체 입금 주소 조회                  | get_coin_addresses         |
|  | 개별 입금 주소 조회                  | get_coin_address           |
|  | 원화 입금하기                      | create_deposit_krw         |
|  | 계정주 확인(트래블룰 검증)가능 거래소 리스트 조회 | get_vasps                  |
|  | 입금 UUID로 트래블룰 검증하기           | verify_travel_rule_by_uuid |
|  | 입금 TxID로 트래블룰 검증하기           | verify_travel_rule_by_txid |
| 서비스 정보 | 입출금 현황                       | get_wallet_status          |
|  | API 키 리스트 조회                 | get_api_keys               |
| 시세 종목 조회 | 마켓 코드 조회                     | get_markets                |
| 시세 캔들 조회 | 초(Second) 캔들                 | get_candles_second         |
|  | 분(Minute) 캔들                 | get_candles_minute         |
|  | 일(Day) 캔들                    | get_candles_day            |
|  | 주(Week) 캔들                   | get_candles_week           |
|  | 월(Month) 캔들                  | get_candles_month          |
|  | 연(Year) 캔들                  | get_candles_year           |
| 시세 체결 조회 | 최근 체결 내역                     | get_trades_ticks           |
| 시세 현재가 조회 | 현재가 정보                       | get_ticker                 |
| 시세 현재가 조회 | 마켓 단위 현재가 정보                 | get_tickers_by_quote       |
| 시세 호가 조회 | 호가 정보                        | get_orderbook              |
|  | 호가 모아보기 단위 정보                        | get_orderbook_levels       |
|  | 호가 정책 조회                        | get_orderbook_instruments       |

### Requests 사용
[Requests][requests] 라이브러리를 사용합니다.


1. `requests.Response` 객체를 그대로 반환합니다.
    
    ```python
    # example.py
    from upbit import Upbit
    
    upbit = Upbit()
    res = upbit.get_markets()
    
    data = res.json()
    status_code = res.status_code
    ```

2. `requests.adapters.HTTPAdapter` 클래스를 사용하여 재시도 횟수 등을 설정할 수 있습니다.

   ```python
   # example.py
   from upbit import Upbit
   import requests
   
   adapter = requests.adapters.HTTPAdapter(max_retries=3)
   
   upbit = Upbit(http_adapter=adapter)
   ```

3. `requests.Session.request` 요청 파라미터 `timeout` 값을 설정할 수 있습니다.

   ```python
   # example.py
   from upbit import Upbit
   
   upbit = Upbit(timeout=(10, 5))  # 모든 요청에 설정할 timeout
   
   res = upbit.get_markets(timeout=10)  # 이 요청에만 설정할 timeout
   ```

### 예외 클래스 제공
모든 API 요청에서 발생한 `requests.exceptions.HTTPError` 예외는 이 예외를 상속한 `upbit.exceptions.UpbitHTTPError` 예외로 발생합니다.

아래 Upbit 공식 문서에 공개한 에러 유형에 맞는 예외 쌍을 가집니다.
* [요청 수 제한](https://docs.upbit.com/docs/user-request-guide)
* [API 주요 에러 코드 목록](https://docs.upbit.com/docs/api-%EC%A3%BC%EC%9A%94-%EC%97%90%EB%9F%AC-%EC%BD%94%EB%93%9C-%EB%AA%A9%EB%A1%9D)

```python
# example.py
from upbit import Upbit, TooManyRequests, UpbitClientError, UpbitServerError

upbit = Upbit()
try:
    res = upbit.get_markets()
except TooManyRequests as e:
    status_code = e.response.status_code  # 429
    # ...예외 처리 코드
except UpbitClientError as e:
    res = e.response
    # ...예외 처리 코드
except UpbitServerError as e:
    res = e.response
    # ...예외 처리 코드
```

### 잔여 요청 수 확인
업비트 API `Remaining-Req` 응답 헤더에 담긴 잔여 요청 수를 `upbit.models.RemainingReq` 객체로 제공되어 정보에 쉽게 접근 할 수 있습니다.
요청 그룹별 최신 값을 프로퍼티에 저장하며 `get_remaining_reqs()` 함수를 호출하면 그룹의 최신 잔여 요청 수 객체를 확인 할 수 있습니다.

참고: [Exchange API 잔여 요청 수 확인 방법](https://docs.upbit.com/docs/user-request-guide#exchange-api-%EC%9E%94%EC%97%AC-%EC%9A%94%EC%B2%AD-%EC%88%98-%ED%99%95%EC%9D%B8-%EB%B0%A9%EB%B2%95)

```python
# example.py
from upbit import Upbit
from upbit.models import RemainingReq

upbit = Upbit()
res = upbit.get_candles_day('KRW-BTC')
rr: RemainingReq = upbit.get_remaining_reqs('candles')
rr.minute
rr.updated

# 응답 헤더도 그대로 사용 가능
rr_text = res.headers['Remaining-Req']  # 'group=candles; min=59; sec=4'
```

### 요청 파라미터 모델 제공
Upbit API 요청 파라미터에 사용할 다양한 데이터 모델을 타입으로 제공합니다.

```python
# example.py
from upbit.models import OrderSide

# ...

# Type Hint
order_side: OrderSide = 'bid'
res = upbit.create_order(market='KRW-BTC', side=order_side, ord_type='limit', price='100', volume='0.01')
```

### Docstring & Type Hint
잘 작성한 Docstring 내용과 타입으로 IDE에서 사용하기 편리합니다. 📝💡


## WebSocket
아직 지원하지 않습니다. [참고 이슈](https://github.com/designmeme/python-upbit-api/issues/7)


## Changelog
최신 변경 사항은 아래에서 확인할 수 있습니다.

- [CHANGELOG.md][changelog]
- [PyPI Releases][releases]


[pypi]: https://pypi.org/project/python-upbit-api/
[releases]: https://pypi.org/project/python-upbit-api/#history
[changelog]: https://github.com/designmeme/python-upbit-api/blob/main/CHANGELOG.md
[license]: https://github.com/designmeme/python-upbit-api/blob/main/LICENSE
[downloads]: https://pypistats.org/packages/python-upbit-api
[requests]: https://requests.readthedocs.io/en/latest/
[upbit docs api]: https://docs.upbit.com/reference/


