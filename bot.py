#!/usr/bin/env python3
"""
TG-Lion Market Bot — Full System with Cloudflare D1 Database
Auto-Deposit · Purchase · Profit Margin · Admin Panel · Premium UI · Persistent Storage
"""

from __future__ import annotations

import html
import http.server
import json
import os
import re
import socketserver
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from typing import Any

# ═══════════════════════════════════════════════════════════════════
# ─── CONFIGURATION (from environment) ───
# ═══════════════════════════════════════════════════════════════════

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TG_LION_API_KEY = os.getenv("TG_LION_API_KEY", "")
TG_LION_USER_ID = os.getenv("TG_LION_USER_ID", "")

WORKER_URL = os.getenv("WORKER_URL", "")
WORKER_TOKEN = os.getenv("WORKER_TOKEN", "")

TRC20_ADDRESS = os.getenv("TRC20_ADDRESS", "")
TRC20_CONTRACT = os.getenv("TRC20_CONTRACT", "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t")

EVM_ADDRESS = os.getenv("EVM_ADDRESS", "")
ERC20_CONTRACT = os.getenv("ERC20_CONTRACT", "0xdAC17F958D2ee523a2206206994597C13D831ec7")
BEP20_CONTRACT = os.getenv("BEP20_CONTRACT", "0x55d398326f99059fF775485246999027B3197955")

SOL_ADDRESS = os.getenv("SOL_ADDRESS", "")
SOL_USDC_MINT = os.getenv("SOL_USDC_MINT", "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")

TRONGRID_API_KEY = os.getenv("TRONGRID_API_KEY", "")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")
SOL_RPC_URL = os.getenv("SOL_RPC_URL", "")
BSC_RPC_URL = os.getenv("BSC_RPC_URL", "")

ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
MIN_DEPOSIT = float(os.getenv("MIN_DEPOSIT", "2.00"))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "60"))
INVOICE_EXPIRY_SECONDS = int(os.getenv("INVOICE_EXPIRY_SECONDS", "3600"))
SUPPORT_URL = os.getenv("SUPPORT_URL", "https://t.me/YourSupportHandle")

# ═══════════════════════════════════════════════════════════════════
# ─── PREMIUM EMOJI IDs ───
# ═══════════════════════════════════════════════════════════════════

PREMIUM_CART_ID = "5330237710655306682"
PREMIUM_WALLET_ID = "6321327299975193112"
PREMIUM_ORDERS_ID = "6323577059679411036"
PREMIUM_PROFILE_ID = "6321081949968408088"
PREMIUM_SUPPORT_ID = "6321290835702848605"
PREMIUM_BACK_ID = "5346230992044574063"

PREMIUM_TRC20_ID = "5249397011576285879"
PREMIUM_ERC20_ID = "5249397011576285879"
PREMIUM_BEP20_ID = "5249397011576285879"
PREMIUM_ETH_ID = "5253656592636733661"
PREMIUM_SOL_ID = "5251414920355931519"

PREMIUM_BALANCE_ID = "6321023044491944284"
PREMIUM_SEARCH_ID = "6320891313550008431"
PREMIUM_ORDERS_HEADER_ID = "6321311215322669245"
PREMIUM_DEPOSIT_ID = "5343777479091831702"
PREMIUM_PRICE_ID = "6321327299975193112"
PREMIUM_STOCK_ID = "5350291836378307462"

PREMIUM_ADMIN_HEADER_ID = "6321147508349216659"
PREMIUM_USERS_ID = "6321311215322669245"
PREMIUM_BAN_ID = "6320947418707794947"
PREMIUM_BROADCAST_ID = "6320924792820081741"

PAGE_PREMIUM_EMOJIS: dict[int, str] = {
    1: "5235776368905562305", 2: "5237704680372447424", 3: "5238044171767393675",
    4: "5235533321001250232", 5: "5238171599152097811", 6: "5235500881113263583",
    7: "5237875542761417785", 8: "5238067300166281132", 9: "5237872922831367023",
    10: "",
}

COUNTRY_PREMIUM_EMOJIS: dict[str, str] = {
    "IN": "", "US": "", "NG": "", "BD": "", "CO": "", "ID": "",
    "NE": "", "ET": "", "AF": "", "PH": "", "KE": "", "CL": "",
    "ZA": "", "GB": "", "MA": "", "PK": "", "UG": "", "NA": "", "YE": "",
}

# ═══════════════════════════════════════════════════════════════════
# ─── LOCAL STATE (only ephemeral UI selections) ───
# ═══════════════════════════════════════════════════════════════════

pending_custom_quantity: dict[int, str] = {}
pending_custom_deposit: dict[int, bool] = {}
pending_admin_input: dict[int, dict[str, Any]] = {}
pending_deposit_selection: dict[int, dict[str, Any]] = {}

profit_margin: float = 0.50

last_processed_tx: dict[str, str | None] = {
    "trc20": None, "erc20": None, "bep20": None, "eth": None, "sol": None,
}
last_bsc_block: int | None = None


@dataclass(frozen=True)
class Country:
    code: str
    name: str
    quantity: int
    price_usd: float


@dataclass
class Order:
    order_id: str
    telegram_user_id: int
    country_code: str
    country_name: str
    quantity: int
    amount_usd: float
    base_cost: float
    profit: float
    status: str
    payment_method: str
    created_at: str


# ═══════════════════════════════════════════════════════════════════
# ─── HEALTH SERVER (for Render port scan) ───
# ═══════════════════════════════════════════════════════════════════

def start_health_server() -> None:
    port = int(os.getenv("PORT", "10000"))

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Bot is running")

        def log_message(self, *args):
            pass

    try:
        with socketserver.TCPServer(("0.0.0.0", port), Handler) as httpd:
            print(f"[Health] Listening on port {port}", flush=True)
            httpd.serve_forever()
    except Exception as e:
        print(f"[Health] Server error: {e}", flush=True)


# ═══════════════════════════════════════════════════════════════════
# ─── WORKER / D1 API ───
# ═══════════════════════════════════════════════════════════════════

def db_call(path: str, payload: dict | None = None, timeout: int = 15) -> dict:
    url = f"{WORKER_URL}/{path}"
    body = json.dumps(payload or {}).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={
        "Authorization": f"Bearer {WORKER_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "TG-Lion-Bot/2.0",
    }, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"[DB] {path} HTTP {e.code}", flush=True)
        return {"error": str(e)}
    except Exception as e:
        print(f"[DB] {path} error: {e}", flush=True)
        return {"error": str(e)}


def db_user_upsert(user_id: int, first_name: str | None = None) -> None:
    db_call("user/upsert", {"user_id": user_id, "first_name": first_name or ""})

def db_user_get(user_id: int) -> dict | None:
    return db_call("user/get", {"user_id": user_id}).get("user")

def db_user_add_balance(user_id: int, delta: float) -> float:
    return db_call("user/add_balance", {"user_id": user_id, "delta": delta}).get("balance", 0.0)

def db_user_set_balance(user_id: int, balance: float) -> None:
    db_call("user/set_balance", {"user_id": user_id, "balance": balance})

def db_user_ban(user_id: int, banned: bool) -> None:
    db_call("user/ban" if banned else "user/unban", {"user_id": user_id})

def db_user_all() -> list[dict]:
    return db_call("user/all", {}).get("users", [])


def db_order_create(order: Order) -> None:
    db_call("order/create", {
        "order_id": order.order_id, "user_id": order.telegram_user_id,
        "country_code": order.country_code, "country_name": order.country_name,
        "quantity": order.quantity, "amount_usd": order.amount_usd,
        "base_cost": order.base_cost, "profit": order.profit,
        "status": order.status, "payment_method": order.payment_method,
        "created_at": int(order.created_at),
    })

def db_order_update_status(order_id: str, status: str) -> None:
    db_call("order/update", {"order_id": order_id, "status": status})

def db_order_list(user_id: int, limit: int = 8) -> list[dict]:
    return db_call("order/list", {"user_id": user_id, "limit": limit}).get("orders", [])

def db_order_recent() -> list[dict]:
    return db_call("order/recent", {}).get("orders", [])

def db_order_count() -> int:
    return db_call("order/count", {}).get("count", 0)


def db_number_save(order_id: str, phone: str, code: str | None = None, password: str | None = None) -> None:
    db_call("number/save", {"order_id": order_id, "phone": phone, "code": code, "password": password})

def db_number_list(order_id: str) -> list[dict]:
    return db_call("number/list", {"order_id": order_id}).get("numbers", [])

def db_number_mark(number_id: int, code: str, password: str) -> None:
    db_call("number/mark", {"id": number_id, "code": code, "password": password})


def db_pending_create(amount: float, user_id: int) -> None:
    db_call("pending/create", {"amount": amount, "user_id": user_id})

def db_pending_consume(amount: float) -> int | None:
    return db_call("pending/consume", {"amount": amount}).get("user_id")

def db_pending_cleanup() -> None:
    db_call("pending/cleanup", {})

def db_deposit_log(user_id: int, chain: str, tx_hash: str, amount: float) -> bool:
    result = db_call("deposit/log", {"user_id": user_id, "chain": chain,
                                     "tx_hash": tx_hash, "amount": amount})
    return not result.get("already", False)


def db_settings_get(key: str) -> str | None:
    return db_call("settings/get", {"key": key}).get("value")

def db_settings_set(key: str, value: str) -> None:
    db_call("settings/set", {"key": key, "value": value})


def db_stats_get() -> dict:
    return db_call("stats/get", {}).get("stats", {})

def db_stats_incr(key: str, delta: float) -> None:
    db_call("stats/incr", {"key": key, "delta": delta})


def db_chain_get(chain: str) -> dict:
    return db_call("chain/get", {"chain": chain}).get("state") or {}

def db_chain_set(chain: str, last_tx_id: str | None, last_block: int | None) -> None:
    db_call("chain/set", {"chain": chain, "last_tx_id": last_tx_id, "last_block": last_block})


# ═══════════════════════════════════════════════════════════════════
# ─── CORE HELPERS ───
# ═══════════════════════════════════════════════════════════════════

def request_json(url: str, *, payload: dict | None = None, timeout: int = 35, context: str = "request") -> Any:
    body = None
    headers = {"Accept": "application/json", "User-Agent": "TG-Lion-Bot/1.0"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=headers,
                                     method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = ""
        try:
            b = json.loads(error.read().decode("utf-8"))
            if isinstance(b, dict):
                m = b.get("message") or b.get("error") or b.get("detail")
                if m:
                    detail = f" {m}"
        except Exception:
            pass
        raise RuntimeError(f"{context} failed: HTTP {error.code}.{detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"{context} network error: {getattr(error, 'reason', 'unknown')}") from error
    except Exception as error:
        raise RuntimeError(f"{context} error: {error}") from error


def telegram(method: str, payload: dict | None = None) -> Any:
    response = request_json(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}",
                            payload=payload or {}, timeout=40, context=f"Telegram {method}")
    if not response.get("ok"):
        raise RuntimeError(f"Telegram API request failed for {method}.")
    return response.get("result")


def tg_lion(action: str, extra: dict[str, str] | None = None) -> Any:
    params = {"action": action, "apiKey": TG_LION_API_KEY, "YourID": TG_LION_USER_ID}
    params.update(extra or {})
    url = f"https://tg-lion.net/?{urllib.parse.urlencode(params)}"
    return request_json(url, timeout=25, context=f"TG-Lion {action}")


def escape(value: Any) -> str:
    return html.escape(str(value), quote=False)


def money(value: float) -> str:
    return f"${value:.2f}"


def pemoji(emoji_id: str | None, fallback: str) -> str:
    if not emoji_id or not str(emoji_id).isdigit():
        return fallback
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'


def get_flag_emoji(code: str) -> str:
    c = code.upper()
    if len(c) != 2:
        return ""
    return chr(0x1F1E6 + ord(c[0]) - ord("A")) + chr(0x1F1E6 + ord(c[1]) - ord("A"))


def error_text(error: Exception) -> str:
    return str(error) or "The service is temporarily unavailable."


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def apply_margin(base_price: float) -> float:
    return round(base_price * (1 + profit_margin), 2)


def register_user(user_id: int, first_name: str | None) -> None:
    try:
        db_user_upsert(user_id, first_name)
    except Exception as e:
        print(f"[DB] register_user error: {e}", flush=True)


def get_balance(user_id: int) -> float:
    u = db_user_get(user_id)
    return float(u.get("balance", 0.0)) if u else 0.0


def is_banned(user_id: int) -> bool:
    u = db_user_get(user_id)
    return bool(u and u.get("banned"))


def add_balance(user_id: int, delta: float) -> float:
    return float(db_user_add_balance(user_id, delta))


# ═══════════════════════════════════════════════════════════════════
# ─── TELEGRAM MESSAGING ───
# ═══════════════════════════════════════════════════════════════════

def send_message(chat_id: int, text: str, reply_markup: dict | None = None) -> None:
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    telegram("sendMessage", payload)


def edit_message(chat_id: int, message_id: int, text: str, reply_markup: dict | None = None) -> None:
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    telegram("editMessageText", payload)


# ═══════════════════════════════════════════════════════════════════
# ─── DEPOSIT INVOICE ───
# ═══════════════════════════════════════════════════════════════════

def create_deposit_invoice(user_id: int, requested_amount: float) -> float:
    if requested_amount < MIN_DEPOSIT:
        requested_amount = MIN_DEPOSIT
    db_pending_cleanup()
    base_suffix = user_id % 100 or 1
    for offset in range(100):
        suffix = (base_suffix + offset) % 100 or 100
        candidate = round(requested_amount + suffix / 100, 2)
        existing = db_pending_consume(candidate)
        if existing is None:
            db_pending_create(candidate, user_id)
            return candidate
        db_pending_create(candidate, existing)
    raise RuntimeError("All invoice amounts are in use. Try again later.")


def find_user_by_deposit_amount(amount: float) -> int | None:
    return db_pending_consume(amount)


# ═══════════════════════════════════════════════════════════════════
# ─── CHAIN CHECKERS ───
# ═══════════════════════════════════════════════════════════════════

def check_trc20() -> list[dict]:
    url = (f"https://api.trongrid.io/v1/accounts/{TRC20_ADDRESS}/transactions/trc20"
           f"?limit=20&contract_address={TRC20_CONTRACT}&only_confirmed=true")
    req = urllib.request.Request(url, headers={
        "TRON-PRO-API-KEY": TRONGRID_API_KEY, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"[Deposit] TRC20 error: {e}", flush=True)
        return []
    results = []
    for tx in data.get("data", []):
        if tx.get("to") != TRC20_ADDRESS:
            continue
        results.append({"chain": "trc20", "tx_id": tx["transaction_id"],
                        "amount": int(tx.get("value", "0")) / 1_000_000,
                        "from": tx.get("from")})
    return results


def check_evm_token(base_url, api_key, address, contract, chain, chain_id):
    params = {"chainid": str(chain_id), "module": "account", "action": "tokentx",
              "address": address, "contractaddress": contract, "page": "1",
              "offset": "20", "sort": "desc", "apikey": api_key}
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers={
            "Accept": "application/json", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read().decode("utf-8")
    except Exception as e:
        print(f"[Deposit] {chain} network error: {e}", flush=True)
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print(f"[Deposit] {chain} non-JSON: {raw[:200]}", flush=True)
        return []
    result = data.get("result")
    if not isinstance(result, list):
        print(f"[Deposit] {chain} API error: {data.get('message')} — {result}", flush=True)
        return []
    results = []
    for tx in result:
        if not isinstance(tx, dict):
            continue
        if tx.get("to", "").lower() != address.lower():
            continue
        try:
            decimals = int(tx.get("tokenDecimal", "18"))
            value = int(tx.get("value", "0"))
        except (ValueError, TypeError):
            continue
        results.append({"chain": chain, "tx_id": tx.get("hash", "unknown"),
                        "amount": value / (10 ** decimals), "from": tx.get("from", "unknown")})
    return results


def check_bep20_ankr() -> list[dict]:
    global last_bsc_block
    TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    padded_to = "0x" + "0" * 24 + EVM_ADDRESS[2:].lower()
    try:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []}
        req = urllib.request.Request(BSC_RPC_URL, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            current_block = int(json.loads(r.read())["result"], 16)
    except Exception as e:
        print(f"[Deposit] BEP20 blockNumber error: {e}", flush=True)
        return []
    if last_bsc_block is None:
        last_bsc_block = current_block - 5
    from_block = last_bsc_block + 1
    if from_block > current_block:
        last_bsc_block = current_block
        return []
    payload = {"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs",
               "params": [{"fromBlock": hex(from_block), "toBlock": hex(current_block),
                           "address": BEP20_CONTRACT, "topics": [TRANSFER_TOPIC, None, padded_to]}]}
    try:
        req = urllib.request.Request(BSC_RPC_URL, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
    except Exception as e:
        print(f"[Deposit] BEP20 getLogs error: {e}", flush=True)
        return []
    logs = data.get("result", [])
    results = []
    for log in logs:
        try:
            value = int(log["data"], 16) / 1_000_000
            tx_id = log.get("transactionHash", "unknown")
            from_addr = "0x" + log["topics"][1][-40:]
            results.append({"chain": "bep20", "tx_id": tx_id, "amount": value, "from": from_addr})
        except Exception:
            continue
    last_bsc_block = current_block
    db_chain_set("bep20", None, current_block)
    return results


def check_eth_native() -> list[dict]:
    params = {"chainid": "1", "module": "account", "action": "txlist",
              "address": EVM_ADDRESS, "page": "1", "offset": "20",
              "sort": "desc", "apikey": ETHERSCAN_API_KEY}
    url = f"https://api.etherscan.io/v2/api?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers={
            "Accept": "application/json", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read().decode("utf-8")
    except Exception as e:
        print(f"[Deposit] ETH error: {e}", flush=True)
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    result = data.get("result")
    if not isinstance(result, list):
        return []
    results = []
    for tx in result:
        if not isinstance(tx, dict):
            continue
        if tx.get("to", "").lower() != EVM_ADDRESS.lower():
            continue
        try:
            amount = int(tx.get("value", "0")) / 1e18
        except (ValueError, TypeError):
            continue
        if amount <= 0:
            continue
        results.append({"chain": "eth", "tx_id": tx.get("hash", "unknown"),
                        "amount": amount, "from": tx.get("from", "unknown")})
    return results


def check_sol() -> list[dict]:
    payload = {"jsonrpc": "2.0", "id": 1, "method": "getSignaturesForAddress",
               "params": [SOL_ADDRESS, {"limit": 10}]}
    try:
        req = urllib.request.Request(SOL_RPC_URL, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            sigs = json.loads(r.read()).get("result", [])
    except Exception as e:
        print(f"[Deposit] SOL error: {e}", flush=True)
        return []
    results = []
    for s in sigs:
        tx_payload = {"jsonrpc": "2.0", "id": 1, "method": "getTransaction",
                      "params": [s["signature"], {"encoding": "jsonParsed",
                                                   "maxSupportedTransactionVersion": 0}]}
        try:
            req = urllib.request.Request(SOL_RPC_URL, data=json.dumps(tx_payload).encode(),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                tx = json.loads(r.read()).get("result")
        except Exception:
            continue
        if not tx or not tx.get("meta"):
            continue
        pre = tx["meta"].get("preTokenBalances", [])
        post = tx["meta"].get("postTokenBalances", [])
        pre_b = post_b = 0.0
        for b in pre:
            if b.get("owner") == SOL_ADDRESS and b.get("mint") == SOL_USDC_MINT:
                pre_b = float(b.get("uiTokenAmount", {}).get("uiAmount", 0) or 0)
        for b in post:
            if b.get("owner") == SOL_ADDRESS and b.get("mint") == SOL_USDC_MINT:
                post_b = float(b.get("uiTokenAmount", {}).get("uiAmount", 0) or 0)
        received = post_b - pre_b
        if received > 0:
            results.append({"chain": "sol", "tx_id": s["signature"],
                            "amount": received, "from": "unknown"})
    return results


# ═══════════════════════════════════════════════════════════════════
# ─── AUTO-DEPOSIT WORKER ───
# ═══════════════════════════════════════════════════════════════════

def auto_deposit_worker() -> None:
    global last_processed_tx, last_bsc_block
    print("[Deposit Worker] Started. Polling every 60 seconds.", flush=True)

    try:
        for chain in ["trc20", "erc20", "bep20", "eth", "sol"]:
            st = db_chain_get(chain)
            if st:
                last_processed_tx[chain] = st.get("last_tx_id")
                if chain == "bep20" and st.get("last_block"):
                    last_bsc_block = int(st["last_block"])
        print("[Deposit Worker] Chain state restored.", flush=True)
    except Exception as e:
        print(f"[Deposit Worker] Failed to restore state: {e}", flush=True)

    while True:
        try:
            _cleanup_expired_invoices()
            all_deposits = []
            for name, fn in [
                ("TRC20", check_trc20),
                ("ERC20", lambda: check_evm_token(
                    "https://api.etherscan.io/v2/api", ETHERSCAN_API_KEY,
                    EVM_ADDRESS, ERC20_CONTRACT, "erc20", 1)),
                ("BEP20", check_bep20_ankr),
                ("ETH", check_eth_native),
                ("SOL", check_sol),
            ]:
                try:
                    all_deposits.extend(fn())
                except Exception as e:
                    print(f"[Deposit Worker] {name} failed: {e}", flush=True)

            for dep in all_deposits:
                chain, tx_id, amount = dep["chain"], dep["tx_id"], dep["amount"]
                if last_processed_tx.get(chain) == tx_id:
                    continue
                user_id = find_user_by_deposit_amount(amount)
                if user_id:
                    new_bal = add_balance(user_id, amount)
                    db_deposit_log(user_id, chain, tx_id, amount)
                    db_stats_incr("total_deposits", amount)
                    try:
                        send_message(user_id,
                            f"✅ <b>Deposit Confirmed!</b>\n\n"
                            f"<b>Chain:</b> {chain.upper()}\n"
                            f"<b>Amount:</b> ${amount:.2f}\n"
                            f"<b>New Balance:</b> ${new_bal:.2f}\n\n"
                            f"<i>TX: {tx_id[:12]}...</i>")
                    except Exception:
                        pass
                    print(f"[Deposit Worker] Credited ${amount:.2f} to {user_id} ({chain})", flush=True)
                last_processed_tx[chain] = tx_id
                db_chain_set(chain, tx_id, None)
        except Exception as e:
            print(f"[Deposit Worker] Error: {e}", flush=True)
        time.sleep(POLL_INTERVAL)


def _cleanup_expired_invoices() -> None:
    try:
        db_pending_cleanup()
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════
# ─── COUNTRIES / TG-LION ───
# ═══════════════════════════════════════════════════════════════════

def get_countries() -> list[Country]:
    response = tg_lion("available_countries")
    raw = response.get("countries", {})
    countries = []
    if not isinstance(raw, dict):
        return countries
    for fallback, val in raw.items():
        if not isinstance(val, dict):
            continue
        code = str(val.get("code") or fallback).strip().upper()
        name = str(val.get("name") or fallback).strip()
        try:
            qty, price = int(val["qty"]), float(val["price"])
        except (KeyError, TypeError, ValueError):
            continue
        if code and name and qty >= 0 and price >= 0:
            countries.append(Country(code, name, qty, price))
    return sorted(countries, key=lambda c: c.price_usd)


def find_country(code: str) -> Country | None:
    return next((c for c in get_countries() if c.code == code.upper()), None)


def buy_number(country_code: str) -> dict:
    resp = tg_lion("getNumber", {"country_code": country_code.lower()})
    if resp.get("status") != "ok":
        raise RuntimeError(f"TG-Lion rejected: {resp.get('message', 'Unknown')}")
    if not resp.get("Number"):
        raise RuntimeError("TG-Lion did not return a phone number.")
    if "new_balance" in resp:
        print(f"[TG-Lion] Owner balance: {resp['new_balance']}", flush=True)
    return {"status": resp["status"], "name": resp.get("name"),
            "Number": resp["Number"], "price": resp.get("price")}


def fetch_code(phone: str, max_attempts: int = 20, delay: int = 5) -> dict:
    for _ in range(max_attempts):
        resp = tg_lion("getCode", {"number": phone})
        status = resp.get("status")
        if status == "ok" and resp.get("code"):
            return {"status": "ok", "Number": resp.get("Number", phone),
                    "code": resp["code"], "pass": resp.get("pass", "N/A")}
        if status in ("wait", "pending", "waiting"):
            time.sleep(delay)
            continue
        if status == "error":
            raise RuntimeError(f"TG-Lion getCode error: {resp.get('message', 'Unknown')}")
        time.sleep(delay)
    raise RuntimeError(f"Code not received for {phone} after {max_attempts * delay}s.")


# ═══════════════════════════════════════════════════════════════════
# ─── KEYBOARDS ───
# ═══════════════════════════════════════════════════════════════════

def main_menu_keyboard(user_id: int | None = None) -> dict:
    rows = [
        [{"text": " Browse Accounts", "callback_data": "menu:countries", "icon_custom_emoji_id": PREMIUM_CART_ID}],
        [{"text": " Wallet", "callback_data": "menu:wallet", "icon_custom_emoji_id": PREMIUM_WALLET_ID},
         {"text": " My Orders", "callback_data": "menu:orders", "icon_custom_emoji_id": PREMIUM_ORDERS_ID}],
        [{"text": " Profile", "callback_data": "menu:profile", "icon_custom_emoji_id": PREMIUM_PROFILE_ID}],
        [{"text": " Support", "url": SUPPORT_URL, "icon_custom_emoji_id": PREMIUM_SUPPORT_ID}],
    ]
    if user_id and is_admin(user_id):
        rows.append([{"text": "🛠 Admin Panel", "callback_data": "admin:panel"}])
    return {"inline_keyboard": rows}


def back_keyboard() -> dict:
    return {"inline_keyboard": [
        [{"text": "Back to Home", "callback_data": "menu:home", "icon_custom_emoji_id": PREMIUM_BACK_ID}],
    ]}


def back_to_countries_keyboard() -> dict:
    return {"inline_keyboard": [
        [{"text": "Back to availability", "callback_data": "menu:countries", "icon_custom_emoji_id": PREMIUM_BACK_ID}],
    ]}


def admin_back_keyboard() -> dict:
    return {"inline_keyboard": [
        [{"text": "🛠 Back to Admin", "callback_data": "admin:panel"}],
        [{"text": "Back to Home", "callback_data": "menu:home", "icon_custom_emoji_id": PREMIUM_BACK_ID}],
    ]}


# ═══════════════════════════════════════════════════════════════════
# ─── USER UI SCREENS ───
# ═══════════════════════════════════════════════════════════════════

def send_home(chat_id: int, first_name: str | None = None, user_id: int | None = None) -> None:
    bal = get_balance(user_id) if user_id else 0.0
    text = "\n".join([
        f"{pemoji(PREMIUM_BALANCE_ID, '💰')} <b>Your Balance:</b> {money(bal)}",
        "👇 Select an option from the menu below:",
        "",
        f"{pemoji(PREMIUM_SEARCH_ID, '✅')} Browse and purchase verified",
        "Telegram accounts.",
        "⚡️ Instant delivery · Secure checkout ·",
        "24/7 support",
    ])
    send_message(chat_id, text, main_menu_keyboard(user_id))


def send_countries(chat_id: int, page: int = 1, message_id: int | None = None) -> None:
    try:
        all_c = get_countries()
        if not all_c:
            raise RuntimeError("TG-Lion returned no available countries.")
        PER = 18
        total_pages = (len(all_c) + PER - 1) // PER
        page = max(1, min(page, total_pages))
        start = (page - 1) * PER
        page_c = all_c[start:start + PER]
        rows = []
        for i in range(0, len(page_c), 2):
            row = []
            for c in page_c[i:i + 2]:
                shown_price = apply_margin(c.price_usd)
                btn = {"text": f"{get_flag_emoji(c.code)} {c.code} · {money(shown_price)}",
                       "callback_data": f"country:{c.code}"}
                if COUNTRY_PREMIUM_EMOJIS.get(c.code):
                    btn["icon_custom_emoji_id"] = COUNTRY_PREMIUM_EMOJIS[c.code]
                row.append(btn)
            rows.append(row)
        pag = []
        for p in range(1, total_pages + 1):
            btn = {"text": f"• {p} •" if p == page else str(p), "callback_data": f"page:{p}"}
            if PAGE_PREMIUM_EMOJIS.get(p):
                btn["icon_custom_emoji_id"] = PAGE_PREMIUM_EMOJIS[p]
            pag.append(btn)
        if pag:
            rows.append(pag)
        rows.append([{"text": "Back to Home", "callback_data": "menu:home",
                      "icon_custom_emoji_id": PREMIUM_BACK_ID}])
        text = "\n".join([
            f"{pemoji(PREMIUM_SEARCH_ID, '📦')} <b>Available inventory</b>", "",
            "Select a country to view live quantity and submit a request.", "",
            f"<i>Page {page} of {total_pages} · Showing {len(page_c)} of {len(all_c)} countries</i>",
        ])
        if message_id:
            edit_message(chat_id, message_id, text, {"inline_keyboard": rows})
        else:
            send_message(chat_id, text, {"inline_keyboard": rows})
    except Exception as e:
        send_message(chat_id, error_text(e), back_keyboard())


def send_country(chat_id: int, code: str) -> None:
    try:
        c = find_country(code)
        if not c:
            raise RuntimeError("That option is no longer available.")
        shown_price = apply_margin(c.price_usd)
        rows = [
            [{"text": "Enter Custom Quantity", "callback_data": f"customqty:{c.code}"}],
            [{"text": "Back to availability", "callback_data": "menu:countries",
              "icon_custom_emoji_id": PREMIUM_BACK_ID}],
            [{"text": "Back to Home", "callback_data": "menu:home",
              "icon_custom_emoji_id": PREMIUM_BACK_ID}],
        ]
        text = "\n".join([
            f"<b>{escape(c.name)} {get_flag_emoji(c.code)}</b>", "",
            f"{pemoji(PREMIUM_PRICE_ID, '💵')} <b>Price per account:</b> {money(shown_price)}",
            f"{pemoji(PREMIUM_STOCK_ID, '📦')} <b>Available stock:</b> {c.quantity:,}", "",
            "👇 Tap below to enter your desired quantity.",
        ])
        send_message(chat_id, text, {"inline_keyboard": rows})
    except Exception as e:
        send_message(chat_id, error_text(e), back_keyboard())


def prompt_custom_quantity(chat_id: int, user_id: int, code: str) -> None:
    try:
        c = find_country(code)
        if not c:
            raise RuntimeError("That option is no longer available.")
        pending_custom_quantity[user_id] = code
        shown_price = apply_margin(c.price_usd)
        text = "\n".join([
            f"<b>{escape(c.name)} {get_flag_emoji(c.code)}</b>", "",
            f"<b>Price per account:</b> {money(shown_price)}",
            f"<b>Available stock:</b> {c.quantity:,}", "",
            "✏️ <b>Send the quantity</b> you want to purchase as a number.", "",
            "<i>Example: 3</i>",
        ])
        send_message(chat_id, text, back_to_countries_keyboard())
    except Exception as e:
        send_message(chat_id, error_text(e), back_keyboard())


def send_wallet(chat_id: int, user_id: int) -> None:
    bal = get_balance(user_id)
    rows = [
        [{"text": "Deposit Funds", "callback_data": "deposit:prompt",
          "icon_custom_emoji_id": PREMIUM_WALLET_ID}],
        [{"text": "Back to Home", "callback_data": "menu:home",
          "icon_custom_emoji_id": PREMIUM_BACK_ID}],
    ]
    text = "\n".join([
        f"{pemoji(PREMIUM_BALANCE_ID, '💳')} <b>Your Wallet</b>", "",
        f"<b>Balance:</b> {money(bal)}", "",
        "Tap <b>Deposit Funds</b> to add balance.",
    ])
    send_message(chat_id, text, {"inline_keyboard": rows})


def prompt_deposit_amount(chat_id: int) -> None:
    text = "\n".join([
        f"{pemoji(PREMIUM_DEPOSIT_ID, '💳')} <b>Deposit Funds</b>", "",
        "✏️ <b>Enter the amount</b> you want to deposit as a number.", "",
        f"<i>Minimum: {money(MIN_DEPOSIT)}</i>",
        "<i>Example: 5</i>",
    ])
    send_message(chat_id, text, back_keyboard())


def send_deposit_network_menu(chat_id: int, amount: float) -> None:
    rows = [
        [{"text": "TRC20 (Tron) — USDT", "callback_data": "chain:trc20",
          "icon_custom_emoji_id": PREMIUM_TRC20_ID}],
        [{"text": "BEP20 (BNB Chain) — USDT", "callback_data": "chain:bep20",
          "icon_custom_emoji_id": PREMIUM_BEP20_ID}],
        [{"text": "ERC20 (Ethereum) — USDT", "callback_data": "chain:erc20",
          "icon_custom_emoji_id": PREMIUM_ERC20_ID}],
        [{"text": "ETH (Ethereum) — Native", "callback_data": "chain:eth",
          "icon_custom_emoji_id": PREMIUM_ETH_ID}],
        [{"text": "SOL (Solana) — USDC", "callback_data": "chain:sol",
          "icon_custom_emoji_id": PREMIUM_SOL_ID}],
        [{"text": "Back to Home", "callback_data": "menu:home",
          "icon_custom_emoji_id": PREMIUM_BACK_ID}],
    ]
    text = "\n".join([
        f"{pemoji(PREMIUM_DEPOSIT_ID, '💳')} <b>Deposit Funds</b>", "",
        f"Amount: <b>${amount:.2f}</b>", "",
        "👇 Select your network:",
    ])
    send_message(chat_id, text, {"inline_keyboard": rows})


def send_deposit_address(chat_id: int, user_id: int, amount: float, chain: str) -> None:
    chain_info = {
        "trc20": ("TRC20 (Tron) — USDT", TRC20_ADDRESS),
        "bep20": ("BEP20 (BNB Chain) — USDT", EVM_ADDRESS),
        "erc20": ("ERC20 (Ethereum) — USDT", EVM_ADDRESS),
        "eth":   ("ETH (Ethereum) — Native", EVM_ADDRESS),
        "sol":   ("SOL (Solana) — USDC", SOL_ADDRESS),
    }
    if chain not in chain_info:
        send_message(chat_id, "❌ Unknown chain.", back_keyboard())
        return
    label, address = chain_info[chain]
    unique = create_deposit_invoice(user_id, amount)
    text = "\n".join([
        f"{pemoji(PREMIUM_DEPOSIT_ID, '💳')} <b>{label}</b>", "",
        f"Send <b>${unique:.2f}</b> to the address below:", "",
        f"<code>{address}</code>", "",
        "⚠️ Send the <b>EXACT</b> amount.",
        "⚠️ Send on the correct network only.",
        "⚠️ Invoice valid for 60 minutes.", "",
        "<i>Balance credited automatically within 1-2 minutes.</i>",
    ])
    rows = [
        [{"text": "Copy Address", "callback_data": f"copydep:{chain}"}],
        [{"text": "Change Network", "callback_data": f"redep:{unique:.2f}",
          "icon_custom_emoji_id": PREMIUM_BACK_ID}],
        [{"text": "Back to Home", "callback_data": "menu:home",
          "icon_custom_emoji_id": PREMIUM_BACK_ID}],
    ]
    send_message(chat_id, text, {"inline_keyboard": rows})


def send_orders(chat_id: int, user_id: int) -> None:
    rows = db_order_list(user_id, limit=8)
    if not rows:
        send_message(
            chat_id,
            f"{pemoji(PREMIUM_ORDERS_HEADER_ID, '📦')} <b>No orders yet</b>\n\n"
            f"Browse availability to start a request.",
            back_keyboard(),
        )
        return
    lines = [
        f"<b>{escape(r['order_id'])}</b>\n"
        f"{escape(r['country_name'])} · {r['quantity']} pc · {money(r['amount_usd'])}\n"
        f"Status: {r['status']}"
        for r in rows
    ]
    send_message(
        chat_id,
        f"{pemoji(PREMIUM_ORDERS_HEADER_ID, '📦')} <b>Your orders</b>\n\n" + "\n\n".join(lines),
        back_keyboard(),
    )


def send_profile(chat_id: int, user_id: int, first_name: str | None = None) -> None:
    u = db_user_get(user_id) or {}
    banned_status = "🚫 Banned" if u.get("banned") else "✅ Active"
    bal = float(u.get("balance", 0.0))
    text = "\n".join([
        f"{pemoji(PREMIUM_PROFILE_ID, '👤')} <b>Profile</b>", "",
        f"<b>Name:</b> {escape(first_name or 'User')}",
        f"<b>ID:</b> <code>{user_id}</code>",
        f"<b>Status:</b> {banned_status}",
        f"<b>Balance:</b> {money(bal)}",
    ])
    send_message(chat_id, text, back_keyboard())


def send_help(chat_id: int) -> None:
    text = "\n".join([
        "<b>How it works</b>", "",
        "1. Browse the live catalog.",
        "2. Select the country and quantity.",
        "3. Confirm your order using your wallet balance.",
        "4. Click 'Get Code' to receive the login code.",
        "5. Use the code and password to log in to Telegram.", "",
        "This bot does not request Telegram passwords or login codes.",
    ])
    send_message(chat_id, text, back_keyboard())


# ═══════════════════════════════════════════════════════════════════
# ─── PURCHASE LOGIC ───
# ═══════════════════════════════════════════════════════════════════

def confirm_order(chat_id: int, user_id: int, code: str, quantity: int) -> None:
    try:
        c = find_country(code)
        if not c:
            raise RuntimeError("That option is no longer available.")
        if quantity < 1:
            raise RuntimeError("Quantity must be at least 1.")
        if quantity > c.quantity:
            raise RuntimeError(f"Only {c.quantity} accounts are available.")
        if quantity > 5:
            raise RuntimeError("Maximum 5 accounts per order.")

        shown_total = apply_margin(c.price_usd) * quantity
        bal = get_balance(user_id)

        rows = []
        if bal >= shown_total:
            rows.append([{"text": "✅ Confirm Purchase", "callback_data": f"confirm:{c.code}:{quantity}"}])
        else:
            rows.append([{"text": "💳 Deposit Funds", "callback_data": "deposit:prompt",
                          "icon_custom_emoji_id": PREMIUM_WALLET_ID}])
        rows.append([{"text": "Change Quantity", "callback_data": f"customqty:{c.code}",
                      "icon_custom_emoji_id": PREMIUM_BACK_ID}])
        rows.append([{"text": "Back to Home", "callback_data": "menu:home",
                      "icon_custom_emoji_id": PREMIUM_BACK_ID}])
        text = "\n".join([
            "<b>🛒 Order Summary</b>", "",
            f"<b>Country:</b> {escape(c.name)} {get_flag_emoji(c.code)} ({c.code})",
            f"<b>Quantity:</b> {quantity} account(s)",
            f"<b>Price per account:</b> {money(apply_margin(c.price_usd))}", "",
            f"<b>Total Price:</b> {money(shown_total)}", "",
            f"<b>Your Wallet Balance:</b> {money(bal)} ({'✅ Sufficient' if bal >= shown_total else '❌ Insufficient'})", "",
            "<i>Click 'Confirm Purchase' to complete your order.</i>" if bal >= shown_total
            else "<i>You don't have enough balance. Please deposit funds first.</i>",
        ])
        send_message(chat_id, text, {"inline_keyboard": rows})
    except Exception as e:
        send_message(chat_id, error_text(e), back_keyboard())


def create_order(chat_id: int, user_id: int, code: str, quantity: int = 1) -> None:
    try:
        c = find_country(code)
        if not c:
            raise RuntimeError("That option is no longer available.")
        if quantity < 1 or quantity > 5:
            raise RuntimeError("Quantity must be between 1 and 5.")
        if quantity > c.quantity:
            raise RuntimeError(f"Only {c.quantity} accounts are available.")

        base_total = c.price_usd * quantity
        shown_total = apply_margin(c.price_usd) * quantity
        profit = round(shown_total - base_total, 2)

        bal = get_balance(user_id)
        if bal < shown_total:
            raise RuntimeError(f"Insufficient balance. Need {money(shown_total)}, have {money(bal)}.")

        add_balance(user_id, -shown_total)

        order = Order(
            order_id=f"TL-{uuid.uuid4().hex[:8].upper()}",
            telegram_user_id=user_id,
            country_code=c.code, country_name=c.name,
            quantity=quantity, amount_usd=shown_total,
            base_cost=base_total, profit=profit,
            status="purchasing", payment_method="wallet",
            created_at=str(int(time.time())),
        )
        db_order_create(order)
        db_stats_incr("total_spent", shown_total)
        db_stats_incr("total_profit", profit)

        send_message(chat_id, f"⏳ <b>Purchasing {quantity} number(s) from {escape(c.name)}...</b>\n\n<i>Please wait.</i>")

        nums = []
        try:
            for _ in range(quantity):
                n = buy_number(c.code)
                nums.append(n)
                db_number_save(order.order_id, n.get("Number", "N/A"))
        except Exception as be:
            add_balance(user_id, shown_total)
            db_stats_incr("total_spent", -shown_total)
            db_stats_incr("total_profit", -profit)
            db_order_update_status(order.order_id, "refunded")
            raise RuntimeError(f"Purchase failed. Refunded {money(shown_total)}.\nReason: {be}")

        db_order_update_status(order.order_id, "awaiting_code")
        details = [f"<b>{i}.</b> <code>{escape(n.get('Number', 'N/A'))}</code>" for i, n in enumerate(nums, 1)]
        rows = [
            [{"text": "📩 Get Code", "callback_data": f"getcode:{order.order_id}:0"}],
            [{"text": "View my orders", "callback_data": "menu:orders"}],
            [{"text": "Back to Home", "callback_data": "menu:home", "icon_custom_emoji_id": PREMIUM_BACK_ID}],
        ]
        text = "\n".join([
            "<b>✅ Numbers Purchased</b>", "",
            f"<b>Order ID:</b> <code>{order.order_id}</code>",
            f"<b>Country:</b> {escape(c.name)}",
            f"<b>Quantity:</b> {quantity}",
            f"<b>Total Paid:</b> {money(shown_total)}",
            f"<b>Your Wallet Balance:</b> {money(get_balance(user_id))}", "",
            "<b>Your Numbers:</b>", *details, "",
            "<i>Click '📩 Get Code' to fetch the login code for each number.</i>",
        ])
        send_message(chat_id, text, {"inline_keyboard": rows})
    except Exception as e:
        send_message(chat_id, error_text(e), back_keyboard())


# ═══════════════════════════════════════════════════════════════════
# ─── ADMIN PANEL ───
# ═══════════════════════════════════════════════════════════════════

def send_admin_panel(chat_id: int) -> None:
    users = db_user_all()
    total_users = len(users)
    total_banned = sum(1 for u in users if u.get("banned"))
    total_orders = db_order_count()
    total_balance = sum(float(u.get("balance", 0)) for u in users)

    stats = db_stats_get()
    total_deposits = stats.get("total_deposits", 0.0)
    total_spent = stats.get("total_spent", 0.0)
    total_profit = stats.get("total_profit", 0.0)

    text = "\n".join([
        f"{pemoji(PREMIUM_ADMIN_HEADER_ID, '🛠')} <b>Admin Panel</b>", "",
        f"{pemoji(PREMIUM_USERS_ID, '👥')} <b>Total Users:</b> {total_users}",
        f"{pemoji(PREMIUM_BAN_ID, '🚫')} <b>Banned Users:</b> {total_banned}",
        f"{pemoji(PREMIUM_ORDERS_ID, '📦')} <b>Total Orders:</b> {total_orders}",
        "",
        f"💰 <b>Total Deposits:</b> {money(total_deposits)}",
        f"🛒 <b>Total Spent:</b> {money(total_spent)}",
        f"📈 <b>Total Profit:</b> {money(total_profit)}",
        f"🏦 <b>User Balances (owed):</b> {money(total_balance)}", "",
        f"⚙️ <b>Profit Margin:</b> {profit_margin * 100:.0f}%", "",
        "<i>Select an action below:</i>",
    ])
    rows = [
        [{"text": "👥 Users", "callback_data": "admin:users"},
         {"text": "📦 Orders", "callback_data": "admin:orders"}],
        [{"text": "💳 Credit User", "callback_data": "admin:credit"},
         {"text": "💸 Debit User", "callback_data": "admin:debit"}],
        [{"text": "🚫 Ban User", "callback_data": "admin:ban"},
         {"text": "✅ Unban User", "callback_data": "admin:unban"}],
        [{"text": "📊 Set Profit Margin", "callback_data": "admin:margin"}],
        [{"text": "Broadcast", "callback_data": "admin:broadcast",
          "icon_custom_emoji_id": PREMIUM_BROADCAST_ID}],
        [{"text": "Back to Home", "callback_data": "menu:home",
          "icon_custom_emoji_id": PREMIUM_BACK_ID}],
    ]
    send_message(chat_id, text, {"inline_keyboard": rows})


def send_admin_users(chat_id: int) -> None:
    users = db_user_all()
    if not users:
        send_message(chat_id, "<b>No users yet.</b>", admin_back_keyboard())
        return
    lines = []
    for u in users[:30]:
        uid = u["user_id"]
        name = u.get("first_name") or "Unknown"
        bal = float(u.get("balance", 0))
        banned = "🚫" if u.get("banned") else "✅"
        lines.append(f"{banned} <code>{uid}</code> — {escape(name)} — {money(bal)}")
    text = "<b>👥 Users (last 30)</b>\n\n" + "\n".join(lines)
    send_message(chat_id, text, admin_back_keyboard())


def send_admin_orders(chat_id: int) -> None:
    rows = db_order_recent()
    if not rows:
        send_message(chat_id, "<b>No orders yet.</b>", admin_back_keyboard())
        return
    lines = []
    for o in rows:
        lines.append(
            f"<b>{escape(o['order_id'])}</b>\n"
            f"User: <code>{o['user_id']}</code>\n"
            f"{escape(o['country_name'])} · {o['quantity']} pc\n"
            f"Paid: {money(o['amount_usd'])} · Cost: {money(o['base_cost'])} · Profit: {money(o['profit'])}\n"
            f"Status: {o['status']}"
        )
    send_message(chat_id, "<b>📦 Recent Orders</b>\n\n" + "\n\n".join(lines), admin_back_keyboard())


def prompt_admin_credit(chat_id: int, admin_id: int) -> None:
    pending_admin_input[admin_id] = {"action": "credit"}
    send_message(chat_id,
        "💳 <b>Credit User</b>\n\nSend in format:\n<code>user_id amount</code>\n\nExample: <code>123456789 5</code>",
        admin_back_keyboard())


def prompt_admin_debit(chat_id: int, admin_id: int) -> None:
    pending_admin_input[admin_id] = {"action": "debit"}
    send_message(chat_id,
        "💸 <b>Debit User</b>\n\nSend in format:\n<code>user_id amount</code>\n\nExample: <code>123456789 2</code>",
        admin_back_keyboard())


def prompt_admin_ban(chat_id: int, admin_id: int) -> None:
    pending_admin_input[admin_id] = {"action": "ban"}
    send_message(chat_id, "🚫 <b>Ban User</b>\n\nSend the user ID to ban.", admin_back_keyboard())


def prompt_admin_unban(chat_id: int, admin_id: int) -> None:
    pending_admin_input[admin_id] = {"action": "unban"}
    send_message(chat_id, "✅ <b>Unban User</b>\n\nSend the user ID to unban.", admin_back_keyboard())


def prompt_admin_margin(chat_id: int, admin_id: int) -> None:
    pending_admin_input[admin_id] = {"action": "margin"}
    send_message(chat_id,
        f"📊 <b>Set Profit Margin</b>\n\nCurrent: <b>{profit_margin * 100:.0f}%</b>\n\n"
        f"Send the new margin as a percentage.\nExample: <code>50</code> for 50%",
        admin_back_keyboard())


def prompt_admin_broadcast(chat_id: int, admin_id: int) -> None:
    pending_admin_input[admin_id] = {"action": "broadcast"}
    send_message(chat_id,
        "📢 <b>Broadcast</b>\n\nSend the message to broadcast.\n\n"
        "Use <code>&lt;emoji:ID&gt;</code> to embed a premium emoji.",
        admin_back_keyboard())


def do_broadcast(chat_id: int, text: str) -> None:
    def replace_emoji(match):
        return f'<tg-emoji emoji-id="{match.group(1)}">⭐</tg-emoji>'
    formatted = re.sub(r"<emoji:(\d+)>", replace_emoji, text)

    users = db_user_all()
    sent = 0
    failed = 0
    for u in users:
        uid = u["user_id"]
        try:
            send_message(uid, f"📢 <b>Announcement</b>\n\n{formatted}")
            sent += 1
            time.sleep(0.05)
        except Exception:
            failed += 1
    send_message(chat_id, f"✅ Broadcast sent to {sent} users.\n❌ Failed: {failed}.",
                 admin_back_keyboard())


# ═══════════════════════════════════════════════════════════════════
# ─── UPDATE HANDLER ───
# ═══════════════════════════════════════════════════════════════════

def handle_update(update: dict) -> None:
    global profit_margin

    cb = update.get("callback_query")
    if cb:
        telegram("answerCallbackQuery", {"callback_query_id": cb["id"]})
        msg = cb.get("message") or {}
        chat_id = (msg.get("chat") or {}).get("id")
        message_id = msg.get("message_id")
        data = cb.get("data")
        if not chat_id or not data:
            return
        parts = data.split(":", 2)
        action = parts[0]
        value = parts[1] if len(parts) > 1 else ""
        extra = parts[2] if len(parts) > 2 else ""
        user = cb.get("from") or {}
        user_id = int(user.get("id", chat_id))

        register_user(user_id, user.get("first_name"))

        u = db_user_get(user_id)
        if u and u.get("banned") and not is_admin(user_id):
            send_message(chat_id, "🚫 You are banned from using this bot.")
            return

        if action == "admin":
            if not is_admin(user_id):
                send_message(chat_id, "❌ Unauthorized.", back_keyboard())
                return
            if value == "panel":      send_admin_panel(chat_id)
            elif value == "users":    send_admin_users(chat_id)
            elif value == "orders":   send_admin_orders(chat_id)
            elif value == "credit":   prompt_admin_credit(chat_id, user_id)
            elif value == "debit":    prompt_admin_debit(chat_id, user_id)
            elif value == "ban":      prompt_admin_ban(chat_id, user_id)
            elif value == "unban":    prompt_admin_unban(chat_id, user_id)
            elif value == "margin":   prompt_admin_margin(chat_id, user_id)
            elif value == "broadcast": prompt_admin_broadcast(chat_id, user_id)
            return

        if action == "menu" and value == "home":
            send_home(chat_id, user.get("first_name"), user_id)
        elif action == "menu" and value == "countries":
            send_countries(chat_id, page=1)
        elif action == "page":
            try:
                send_countries(chat_id, page=int(value), message_id=message_id)
            except ValueError:
                send_countries(chat_id, page=1)
        elif action == "menu" and value == "orders":
            send_orders(chat_id, user_id)
        elif action == "menu" and value == "wallet":
            send_wallet(chat_id, user_id)
        elif action == "menu" and value == "profile":
            send_profile(chat_id, user_id, user.get("first_name"))
        elif action == "deposit" and value == "prompt":
            pending_custom_deposit[user_id] = True
            prompt_deposit_amount(chat_id)
        elif action == "chain" and value:
            sel = pending_deposit_selection.get(user_id, {})
            amt = sel.get("amount")
            if not amt:
                send_message(chat_id, "❌ Session expired. Start over.", back_keyboard())
                return
            send_deposit_address(chat_id, user_id, amt, value)
        elif action == "copydep" and value:
            cinfo = {"trc20": TRC20_ADDRESS, "bep20": EVM_ADDRESS,
                     "erc20": EVM_ADDRESS, "eth": EVM_ADDRESS, "sol": SOL_ADDRESS}
            addr = cinfo.get(value, "unknown")
            send_message(chat_id, f"📋 <b>Address:</b>\n<code>{addr}</code>")
        elif action == "redep" and value:
            try:
                send_deposit_network_menu(chat_id, float(value))
            except ValueError:
                send_wallet(chat_id, user_id)
        elif action == "country" and value:
            send_country(chat_id, value)
        elif action == "customqty" and value:
            prompt_custom_quantity(chat_id, user_id, value)
        elif action == "confirm" and value and extra:
            try:
                create_order(chat_id, user_id, value, int(extra))
            except ValueError:
                send_country(chat_id, value)
        elif action == "getcode" and value and extra:
            try:
                idx = int(extra)
                nums = db_number_list(value)
                if idx >= len(nums):
                    raise RuntimeError("All codes delivered.")
                row = nums[idx]
                phone = row.get("phone")
                send_message(chat_id, f"⏳ <b>Fetching code for</b> <code>{escape(phone)}</code>...")
                try:
                    code_result = fetch_code(phone)
                except Exception as fe:
                    retry = {"inline_keyboard": [
                        [{"text": "🔄 Retry", "callback_data": f"getcode:{value}:{idx}"}],
                        [{"text": "View my orders", "callback_data": "menu:orders"}],
                    ]}
                    send_message(chat_id, f"❌ Failed: {escape(str(fe))}", retry)
                    return

                db_number_mark(row["id"], code_result.get("code", ""), code_result.get("pass", ""))

                next_idx = idx + 1
                has_more = next_idx < len(nums)
                if has_more:
                    btns = [
                        [{"text": f"📩 Get Code for #{next_idx + 1}",
                          "callback_data": f"getcode:{value}:{next_idx}"}],
                        [{"text": "View my orders", "callback_data": "menu:orders"}],
                        [{"text": "Back to Home", "callback_data": "menu:home",
                          "icon_custom_emoji_id": PREMIUM_BACK_ID}],
                    ]
                else:
                    db_order_update_status(value, "completed")
                    btns = [
                        [{"text": "View my orders", "callback_data": "menu:orders"}],
                        [{"text": "Back to Home", "callback_data": "menu:home",
                          "icon_custom_emoji_id": PREMIUM_BACK_ID}],
                    ]
                text = "\n".join([
                    f"✅ <b>Code Received for Account #{idx + 1}</b>", "",
                    f"<b>📱 Number:</b> <code>{escape(phone)}</code>",
                    f"<b>🔑 Code:</b> <code>{escape(str(code_result.get('code')))}</code>",
                    f"<b>🔒 Password:</b> <code>{escape(str(code_result.get('pass')))}</code>",
                ])
                send_message(chat_id, text, {"inline_keyboard": btns})
            except Exception as e:
                send_message(chat_id, error_text(e), back_keyboard())
        return

    # ─── TEXT MESSAGES ───
    message = update.get("message") or {}
    text = message.get("text")
    if not text:
        return
    chat_id = int((message.get("chat") or {})["id"])
    user = message.get("from") or {}
    user_id = int(user.get("id", chat_id))
    command = text.strip().split()[0].lower()

    register_user(user_id, user.get("first_name"))
    u = db_user_get(user_id)
    if u and u.get("banned") and not is_admin(user_id):
        send_message(chat_id, "🚫 You are banned from using this bot.")
        return

    if is_admin(user_id) and user_id in pending_admin_input:
        pending = pending_admin_input.pop(user_id)
        act = pending.get("action")

        if act == "credit":
            try:
                p = text.strip().split()
                target, amt = int(p[0]), float(p[1])
                new_bal = add_balance(target, amt)
                send_message(chat_id, f"✅ Credited {money(amt)} to <code>{target}</code>.\nNew balance: {money(new_bal)}", admin_back_keyboard())
                try:
                    send_message(target, f"💳 <b>Balance Credited</b>\n\n+{money(amt)}\nNew balance: {money(new_bal)}")
                except Exception:
                    pass
            except Exception as e:
                send_message(chat_id, f"❌ Invalid input. {e}", admin_back_keyboard())
            return

        if act == "debit":
            try:
                p = text.strip().split()
                target, amt = int(p[0]), float(p[1])
                new_bal = add_balance(target, -amt)
                if new_bal < 0:
                    db_user_set_balance(target, 0.0)
                    new_bal = 0.0
                send_message(chat_id, f"✅ Debited {money(amt)} from <code>{target}</code>.\nNew balance: {money(new_bal)}", admin_back_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Invalid input. {e}", admin_back_keyboard())
            return

        if act == "ban":
            try:
                target = int(text.strip())
                db_user_ban(target, True)
                send_message(chat_id, f"🚫 Banned <code>{target}</code>.", admin_back_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ {e}", admin_back_keyboard())
            return

        if act == "unban":
            try:
                target = int(text.strip())
                db_user_ban(target, False)
                send_message(chat_id, f"✅ Unbanned <code>{target}</code>.", admin_back_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ {e}", admin_back_keyboard())
            return

        if act == "margin":
            try:
                pct = float(text.strip())
                if pct < 0 or pct > 500:
                    raise ValueError("Margin must be between 0 and 500.")
                profit_margin = pct / 100.0
                db_settings_set("profit_margin", str(profit_margin))
                send_message(chat_id, f"✅ Profit margin set to <b>{pct:.0f}%</b>.", admin_back_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ {e}", admin_back_keyboard())
            return

        if act == "broadcast":
            do_broadcast(chat_id, text)
            return

    if command == "/admin" and is_admin(user_id):
        send_admin_panel(chat_id)
        return

    if user_id in pending_custom_deposit and command not in ("/start", "/menu", "/wallet", "/orders", "/help"):
        del pending_custom_deposit[user_id]
        try:
            amt = float(text.strip())
            if amt < MIN_DEPOSIT:
                raise RuntimeError(f"Minimum deposit is {money(MIN_DEPOSIT)}.")
            pending_deposit_selection[user_id] = {"amount": amt}
            send_deposit_network_menu(chat_id, amt)
        except ValueError:
            send_message(chat_id, "❌ Invalid amount.", back_keyboard())
        return

    if user_id in pending_custom_quantity and command not in ("/start", "/menu", "/orders", "/help"):
        code = pending_custom_quantity.pop(user_id)
        try:
            confirm_order(chat_id, user_id, code, int(text.strip()))
        except ValueError:
            send_message(chat_id, "❌ Invalid quantity.", back_to_countries_keyboard())
        return

    if command in ("/start", "/menu"):
        send_home(chat_id, user.get("first_name"), user_id)
    elif command == "/orders":
        send_orders(chat_id, user_id)
    elif command == "/help":
        send_help(chat_id)
    else:
        send_home(chat_id, user.get("first_name"), user_id)


# ═══════════════════════════════════════════════════════════════════
# ─── MAIN ───
# ═══════════════════════════════════════════════════════════════════

def main() -> None:
    global profit_margin

    # ─── Validate env vars ───
    missing = []
    for name, val in [
        ("TELEGRAM_TOKEN", TELEGRAM_TOKEN),
        ("TG_LION_API_KEY", TG_LION_API_KEY),
        ("TG_LION_USER_ID", TG_LION_USER_ID),
        ("WORKER_URL", WORKER_URL),
        ("WORKER_TOKEN", WORKER_TOKEN),
        ("TRC20_ADDRESS", TRC20_ADDRESS),
        ("EVM_ADDRESS", EVM_ADDRESS),
        ("SOL_ADDRESS", SOL_ADDRESS),
        ("TRONGRID_API_KEY", TRONGRID_API_KEY),
        ("ETHERSCAN_API_KEY", ETHERSCAN_API_KEY),
        ("SOL_RPC_URL", SOL_RPC_URL),
        ("BSC_RPC_URL", BSC_RPC_URL),
    ]:
        if not val:
            missing.append(name)
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}", file=sys.stderr, flush=True)
        sys.exit(1)

    print("TG-Lion Market Bot starting...", flush=True)
    print("Worker URL:", WORKER_URL, flush=True)

    # ─── Start health server FIRST so Render keeps the service alive ───
    threading.Thread(target=start_health_server, daemon=True).start()
    print("[Startup] Health server started.", flush=True)

    try:
        bot_info = telegram("getMe")
        print(f"Telegram verified: @{bot_info.get('username', 'unknown')}", flush=True)
        print(f"TG-Lion verified: {len(get_countries())} countries", flush=True)
    except Exception as e:
        print(f"Startup failed: {error_text(e)}", file=sys.stderr, flush=True)
        sys.exit(1)

    try:
        val = db_settings_get("profit_margin")
        if val:
            profit_margin = float(val)
        print(f"[Startup] Profit margin: {profit_margin * 100:.0f}%", flush=True)
    except Exception as e:
        print(f"[Startup] Could not load margin: {e}", flush=True)

    threading.Thread(target=auto_deposit_worker, daemon=True).start()
    print("[Startup] Deposit worker started.", flush=True)

    offset = None
    while True:
        try:
            payload = {"timeout": 25, "allowed_updates": ["message", "callback_query"]}
            if offset is not None:
                payload["offset"] = offset
            for update in telegram("getUpdates", payload) or []:
                offset = int(update["update_id"]) + 1
                handle_update(update)
        except KeyboardInterrupt:
            print("\nBot stopped.")
            return
        except Exception as e:
            print(error_text(e), file=sys.stderr)
            time.sleep(3)


if __name__ == "__main__":
    main()