# Changelog

## [1.2.1](https://github.com/designmeme/python-upbit-api/compare/v1.2.0...v1.2.1) (2024-02-23)


### Bug Fixes

* __all__ 내용 추가 [#14](https://github.com/designmeme/python-upbit-api/issues/14) ([03c0057](https://github.com/designmeme/python-upbit-api/commit/03c0057684dfa71dfe558a8118602d716840cd22))


### Documentation

* 마켓 코드 조회 응답 예시에 market_event 필드 추가 및 market_warning 필드 삭제 ([58eea2a](https://github.com/designmeme/python-upbit-api/commit/58eea2ad154a0ebe51d4c3302bad0b5d48c9d68c))

## [1.2.0](https://github.com/designmeme/python-upbit-api/compare/v1.1.0...v1.2.0) (2023-11-06)


### Features

* 원화 입출금시 two_factor_type 지원 내용 변경안 반영 [#12](https://github.com/designmeme/python-upbit-api/issues/12) ([fe52bac](https://github.com/designmeme/python-upbit-api/commit/fe52baca45ddbea5884cb39bab9bdc54343c105d))


### Documentation

* 출금 허용 주소 리스트 조회 응답 예시에 network_name 필드 추가 ([1628880](https://github.com/designmeme/python-upbit-api/commit/16288805fd605e0e3f77f6a4e0bdbc67117e548d))

## [1.1.0](https://github.com/designmeme/python-upbit-api/compare/v1.0.1...v1.1.0) (2023-05-23)


### Features

* Keyword-Only Argument(*) 적용 ([fcdd448](https://github.com/designmeme/python-upbit-api/commit/fcdd4487b0801b16642eab489533cdf9dd5ee176))
* 개별 입금 조회 메소드(get_deposit) 응답 예시에 net_type 필드 추가 [#1](https://github.com/designmeme/python-upbit-api/issues/1) ([8f1f36e](https://github.com/designmeme/python-upbit-api/commit/8f1f36e114ccdd8be509948b3305b7d5a83393cc))
* 개별 입금 주소 조회 메서드(get_coin_address)에 파라미터 net_type 추가 [#1](https://github.com/designmeme/python-upbit-api/issues/1) ([1bbe25e](https://github.com/designmeme/python-upbit-api/commit/1bbe25eb433b502b23efb684b5a3118daf959ca1))
* 개별 출금 조회 메소드(get_withdraw) 응답 예시에 net_type 필드 추가 [#1](https://github.com/designmeme/python-upbit-api/issues/1) ([4b84960](https://github.com/designmeme/python-upbit-api/commit/4b8496074538b904cc341b798090ab842963e766))
* 입금 리스트 조회 메소드(get_deposits) 응답 예시에 net_type 필드 추가 [#1](https://github.com/designmeme/python-upbit-api/issues/1) ([d5b1e35](https://github.com/designmeme/python-upbit-api/commit/d5b1e3560eba18ee8a82f157681e2d4e8efe01af))
* 입금 주소 생성 요청 메서드(create_coin_address)에 파라미터 net_type 추가 [#1](https://github.com/designmeme/python-upbit-api/issues/1) ([37d9497](https://github.com/designmeme/python-upbit-api/commit/37d94972487bd72cd94af0fa3c2c5fdf3facac7a))
* 입출금 현황 조회 메소드 get_wallet_status 응답 예시에 net_type 필드 추가 [#1](https://github.com/designmeme/python-upbit-api/issues/1) ([5322894](https://github.com/designmeme/python-upbit-api/commit/5322894f2c9c8fca51ae1663286ab7fe83d7ded7))
* 전체 입금 주소 조회 메소드(get_coin_addresses) 응답 예시에 net_type 필드 추가 [#1](https://github.com/designmeme/python-upbit-api/issues/1) ([db7efd9](https://github.com/designmeme/python-upbit-api/commit/db7efd99eaa6d60b2a485d300470d329153098d2))
* 출금 가능 정보 조회 메서드(get_withdraw_chance)에 파라미터 net_type 추가 [#1](https://github.com/designmeme/python-upbit-api/issues/1) ([19afa7f](https://github.com/designmeme/python-upbit-api/commit/19afa7f3be0dda752c9ca3d22a233e2fbd48550e))
* 출금 리스트 조회 메소드(get_withdraws) 응답 예시에 net_type 필드 추가 [#1](https://github.com/designmeme/python-upbit-api/issues/1) ([e2c5565](https://github.com/designmeme/python-upbit-api/commit/e2c556567946d5b8537ba0dc8f6d61b1d7225116))
* 출금 허용 주소 리스트 조회 메소드 get_withdraw_addresses 추가 [#1](https://github.com/designmeme/python-upbit-api/issues/1) ([c263f5b](https://github.com/designmeme/python-upbit-api/commit/c263f5b597910e221fdc1f3e5ca669a8b377b0fd))
* 코인 출금하기 메서드(create_withdraw_coin)에 파라미터 net_type 추가 [#1](https://github.com/designmeme/python-upbit-api/issues/1) ([fa8c956](https://github.com/designmeme/python-upbit-api/commit/fa8c956083b35dee275d1c410a22bc647b24626e))


### Bug Fixes

* TransactionStatus 모델을 WithdrawState, DepositState 두 개로 분리 ([b945f9d](https://github.com/designmeme/python-upbit-api/commit/b945f9d057cc05cab81c4ac5b77581620050d060))


### Documentation

* **readme:** TooManyRequests 오류 상태 코드를 423에서 429로 수정 ([c27e7e8](https://github.com/designmeme/python-upbit-api/commit/c27e7e83251db6f4b78cbf4d46f6d534dab26f32))
* **readme:** 업비트 REST API 구현 메서드 정보 추가 ([29294d7](https://github.com/designmeme/python-upbit-api/commit/29294d761fd4b2fe63cfc8f827c4c144c61f7450))
* TooManyRequests 오류 상태 코드를 423에서 429로 수정 ([aab65a9](https://github.com/designmeme/python-upbit-api/commit/aab65a9129f5e9b21c07ddac74110c664a34da56))
* **upbit:** '거래 가능한 마켓 목록 조회' 이름을 '마켓 코드 조회'로 변경 ([3dda03b](https://github.com/designmeme/python-upbit-api/commit/3dda03ba5575e70d813e84b63246f2d1d02e2108))
* **upbit:** '코인 출금하기' 이름을 '디지털 자산 출금하기'로 변경 ([4015b0a](https://github.com/designmeme/python-upbit-api/commit/4015b0aae13f50d2a5f1fd35fc9309ec2ccd5d5e))
* 입금 리스트 조회 메서드(get_deposits)에서 파라미터 문구 오류 수정 ([87ce13d](https://github.com/designmeme/python-upbit-api/commit/87ce13d228f71b5a7f1a6f18bc70fe835d738e28))

## [1.0.1](https://github.com/designmeme/python-upbit-api/compare/v1.0.0...v1.0.1) (2023-05-12)


### Bug Fixes

* TooManyRequests 오류 상태 코드를 423에서 429로 수정 ([f8621ea](https://github.com/designmeme/python-upbit-api/commit/f8621eabcf12fc5383137d7beb2711e056a1eff3))
* 거래 API 관련 메소드 호출시 요청 헤더 파라미터가 추가되지 않는 문제 해결 ([1aa28fc](https://github.com/designmeme/python-upbit-api/commit/1aa28fc3a7ff407b3046e04903ada6a73fa77071))

## [1.0.0](https://github.com/designmeme/python-upbit-api/compare/v1.0.0-alpha.2...v1.0.0) (2023-05-11)


### Features

* **exception:** UpbitError 클래스명을 UpbitHTTPError 로 더 명확히 변경 ([bf364e3](https://github.com/designmeme/python-upbit-api/commit/bf364e3b5c07228f8298c29a2b4e82562e73751e))
* **upbit:** Upbit 생성 인자 http_adapter 추가 ([847309b](https://github.com/designmeme/python-upbit-api/commit/847309b5d186773643ba74d4d3ed745a5833c0aa)), closes [#5](https://github.com/designmeme/python-upbit-api/issues/5)
* **upbit:** 업비트 문서에 명시되지 않은 에러가 발생한 경우 UpbitClientError 예외 발생 시키기 ([0fba156](https://github.com/designmeme/python-upbit-api/commit/0fba1568d6314c152e0e50619f0a046ce5bf7000))


### Bug Fixes

* RemainingReq 초기화시 InvalidRemainingReq 예외 발생시키지 않는 문제 해결 ([66de9a6](https://github.com/designmeme/python-upbit-api/commit/66de9a616eaf53e691c59737b1cfff95e2f7dafb))


### Documentation

* **exceptions:** 주석 작성 ([25ee937](https://github.com/designmeme/python-upbit-api/commit/25ee93718205b5d2a060897b6ca99cd038c77b94))
* **readme:** README.md 작성 ([f9fcd59](https://github.com/designmeme/python-upbit-api/commit/f9fcd59d6143adc169d9c403249f82861088fa62))
* 주석 보완 ([708b744](https://github.com/designmeme/python-upbit-api/commit/708b744712e30fa54684cab8b24190635f03af32))
* 주석 수정 ([61e5917](https://github.com/designmeme/python-upbit-api/commit/61e59174f92c83781ce2708121be440c2254a801))


### Miscellaneous Chores

* release 1.0.0 ([21ba69b](https://github.com/designmeme/python-upbit-api/commit/21ba69bf5322da707e7564f41d8f6611e5e1f87f))

## [1.0.0-alpha.2](https://github.com/designmeme/python-upbit-api/compare/v1.0.0-alpha.1...v1.0.0-alpha.2) (2023-05-01)


### Miscellaneous Chores

* release 1.0.0-alpha.2 ([c1e6ded](https://github.com/designmeme/python-upbit-api/commit/c1e6deda85796bdf23de75149bc4ebf4961e37b7))

## [1.0.0-alpha.1](https://github.com/designmeme/python-upbit-api/compare/v1.0.0-alpha...v1.0.0-alpha.1) (2023-05-01)


### Bug Fixes

* install_requires 설정 오류 수정 ([354cb9e](https://github.com/designmeme/python-upbit-api/commit/354cb9e4057bc1266a566d8a9f8684006e9bf80c))


### Miscellaneous Chores

* 안 쓰는 패키지 임포트 삭제 ([9005227](https://github.com/designmeme/python-upbit-api/commit/90052274ebc57831e5ab0e3ea99fd8ce192eee78))

## 1.0.0-alpha (2023-05-01)


### Bug Fixes

* test ([dec6690](https://github.com/designmeme/python-upbit-api/commit/dec6690b6d7c8e8bf268573cac56c8066fc52cfa))


### Miscellaneous Chores

* release 0.1.0-alpha ([f852632](https://github.com/designmeme/python-upbit-api/commit/f852632a4ebd6e6f59eafc52a9abff42f3eef63a))
* release 1.0.0-alpha ([0c36360](https://github.com/designmeme/python-upbit-api/commit/0c3636063788e020c4e8952783897d26ee673f64))
* release 1.0.0-alpha ([069eceb](https://github.com/designmeme/python-upbit-api/commit/069eceb2b89832981ead3ecc1fda48e861adc602))
