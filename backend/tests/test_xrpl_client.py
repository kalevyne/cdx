from unittest.mock import MagicMock

import pytest
from xrpl.utils import str_to_hex
from xrpl.wallet import Wallet

from app.config import get_settings
from app.services import xrpl_client
from app.services.xrpl_client import XrplClient, XrplError, XrplNotConfiguredError

WALLET = Wallet.create()
DESTINATION = Wallet.create().address


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv("XRPL_TESTNET_WALLET_SEED", WALLET.seed)
    monkeypatch.setenv("XRPL_ANCHOR_DESTINATION", DESTINATION)
    get_settings.cache_clear()
    return XrplClient(get_settings())


def _submit_result(outcome: str = "tesSUCCESS") -> MagicMock:
    return MagicMock(
        result={"hash": "ABC", "ledger_index": 42, "meta": {"TransactionResult": outcome}}
    )


def test_anchor_sends_one_drop_payment_with_hex_memos(configured, monkeypatch):
    submit = MagicMock(return_value=_submit_result())
    monkeypatch.setattr(xrpl_client, "submit_and_wait", submit)

    receipt = configured.anchor({"cdx/sha256": "ab" * 32})

    payment = submit.call_args.args[0]
    assert (payment.account, payment.destination, payment.amount) == (
        WALLET.address,
        DESTINATION,
        "1",
    )
    assert payment.memos[0].memo_type == str_to_hex("cdx/sha256")
    assert payment.memos[0].memo_data == str_to_hex("ab" * 32)
    assert (receipt.network, receipt.tx_hash, receipt.ledger_index) == ("testnet", "ABC", 42)


def test_anchor_rejected_by_ledger_raises(configured, monkeypatch):
    monkeypatch.setattr(
        xrpl_client, "submit_and_wait", MagicMock(return_value=_submit_result("tecNO_DST"))
    )

    with pytest.raises(XrplError, match="tecNO_DST"):
        configured.anchor({"cdx/sha256": "x"})


def test_unconfigured_client_refuses_to_anchor():
    client = XrplClient(get_settings())

    assert client.is_configured is False
    with pytest.raises(XrplNotConfiguredError, match="XRPL_TESTNET_WALLET_SEED"):
        client.anchor({})


def test_mainnet_is_refused_until_custody_is_decided(configured, monkeypatch):
    monkeypatch.setenv("XRPL_NETWORK", "mainnet")
    get_settings.cache_clear()

    with pytest.raises(XrplNotConfiguredError, match="DECISIONS.md #6"):
        XrplClient(get_settings()).anchor({})


def test_fetch_memos_decodes_validated_transaction(configured, monkeypatch):
    response = MagicMock()
    response.is_successful.return_value = True
    response.result = {
        "validated": True,
        "tx_json": {
            "Memos": [
                {"Memo": {"MemoType": str_to_hex("cdx/sha256"), "MemoData": str_to_hex("f00d")}}
            ]
        },
    }
    rpc = MagicMock()
    rpc.request.return_value = response
    monkeypatch.setattr(xrpl_client, "JsonRpcClient", lambda url: rpc)

    assert configured.fetch_memos("ABC") == {"cdx/sha256": "f00d"}
