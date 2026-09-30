"""XRPL access: anchoring memos in a transaction, and reading them back.

Anchors are minimal `Payment` transactions (1 drop) carrying CDX's data in
`Memo` fields — decision #9 in docs/DECISIONS.md. Memo contents are stored as
hex-encoded UTF-8 text, so public explorers show the SHA-256 as readable text.
"""

import threading
from dataclasses import dataclass
from functools import lru_cache

from xrpl.clients import JsonRpcClient
from xrpl.models import Memo, Payment, Tx
from xrpl.transaction import submit_and_wait
from xrpl.utils import hex_to_str, str_to_hex
from xrpl.wallet import Wallet

from app.config import Settings, get_settings

_RPC_URLS = {"testnet": "https://s.altnet.rippletest.net:51234/"}
_EXPLORER_TX_URLS = {
    "testnet": "https://testnet.xrpl.org/transactions/{tx_hash}",
    "mainnet": "https://livenet.xrpl.org/transactions/{tx_hash}",
}
_ANCHOR_AMOUNT_DROPS = "1"


class XrplError(Exception):
    """The ledger rejected or couldn't process a request."""


class XrplNotConfiguredError(XrplError):
    """Anchoring isn't set up (no wallet/destination), or the network isn't allowed."""


@dataclass(frozen=True)
class AnchorReceipt:
    network: str
    tx_hash: str
    ledger_index: int


def explorer_tx_url(network: str, tx_hash: str) -> str | None:
    template = _EXPLORER_TX_URLS.get(network)
    return template.format(tx_hash=tx_hash) if template else None


class XrplClient:
    # One anchor at a time: concurrent submits from one account would race for
    # the same account Sequence number.
    _submit_lock = threading.Lock()

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.network = settings.xrpl_network

    @property
    def is_configured(self) -> bool:
        return self._configuration_problem() is None

    def anchor(self, memos: dict[str, str]) -> AnchorReceipt:
        """Submit a Payment carrying `memos` ({type: text}) and wait for validation."""
        problem = self._configuration_problem()
        if problem:
            raise XrplNotConfiguredError(problem)

        wallet = Wallet.from_seed(self._settings.xrpl_testnet_wallet_seed)
        payment = Payment(
            account=wallet.address,
            destination=self._settings.xrpl_anchor_destination,
            amount=_ANCHOR_AMOUNT_DROPS,
            memos=[
                Memo(memo_type=str_to_hex(memo_type), memo_data=str_to_hex(data))
                for memo_type, data in memos.items()
            ],
        )
        try:
            with self._submit_lock:
                result = submit_and_wait(payment, self._rpc_client(), wallet).result
        except Exception as exc:  # xrpl-py raises several unrelated exception types
            raise XrplError(f"XRPL submission failed: {exc}") from exc

        outcome = result.get("meta", {}).get("TransactionResult")
        if outcome != "tesSUCCESS":
            raise XrplError(f"XRPL rejected the anchor transaction: {outcome}")
        return AnchorReceipt(
            network=self.network, tx_hash=result["hash"], ledger_index=result["ledger_index"]
        )

    def fetch_memos(self, tx_hash: str) -> dict[str, str]:
        """The memos ({type: text}) of a validated transaction."""
        try:
            response = self._rpc_client().request(Tx(transaction=tx_hash))
        except Exception as exc:
            raise XrplError(f"Couldn't reach the XRP Ledger: {exc}") from exc
        if not response.is_successful():
            raise XrplError(f"Transaction {tx_hash} not found on the ledger")
        result = response.result
        if not result.get("validated"):
            raise XrplError(f"Transaction {tx_hash} isn't validated yet")
        tx_json = result.get("tx_json", result)  # API v2 nests fields under tx_json
        memos = {}
        for entry in tx_json.get("Memos", []):
            memo = entry.get("Memo", {})
            if "MemoType" in memo:
                memos[hex_to_str(memo["MemoType"])] = hex_to_str(memo.get("MemoData", ""))
        return memos

    def _rpc_client(self) -> JsonRpcClient:
        return JsonRpcClient(_RPC_URLS[self.network])

    def _configuration_problem(self) -> str | None:
        if self.network != "testnet":
            return "Mainnet anchoring isn't enabled: wallet custody is still open (DECISIONS.md #6)"
        if not self._settings.xrpl_testnet_wallet_seed:
            return "XRPL_TESTNET_WALLET_SEED is not set"
        if not self._settings.xrpl_anchor_destination:
            return "XRPL_ANCHOR_DESTINATION is not set"
        return None


@lru_cache
def get_xrpl_client() -> XrplClient:
    return XrplClient(get_settings())
