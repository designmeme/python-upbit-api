# A library that provides a Python interface to the Upbit API
# Copyright 2023
# 이지혜 Lee Jihye <ghe.lee19@gmail.com>
"""A library that provides a Python interface to the Upbit API"""

from .upbit import Upbit

from .exceptions import (
    UpbitHTTPError,
    UpbitClientError,
    UpbitServerError,
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
    InvalidRemainingReq,
)

__all__ = [
    'Upbit',
    'UpbitHTTPError',
    'UpbitClientError',
    'UpbitServerError',
    'TooManyRequests',
    'CreateAskError',
    'CreateBidError',
    'InsufficientFundsAsk',
    'InsufficientFundsBid',
    'UnderMinTotalAsk',
    'UnderMinTotalBid',
    'WithdrawAddressNotRegistered',
    'InvalidParameterError',
    'ValidationError',
    'InvalidQueryPayload',
    'JwtVerification',
    'ExpiredAccessKey',
    'NonceUsed',
    'NoAuthorizationIP',
    'OutOfScope',
    'ApiKeyError',
    'InvalidRemainingReq',
]
