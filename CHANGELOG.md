# Changelog

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
