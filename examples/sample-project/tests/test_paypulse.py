import hmac
import hashlib
import time
from paypulse.webhooks import verify_hmac_signature, WebhookRouter
from paypulse.ledger import Transaction, JournalEntry, LedgerEngine

def test_verify_hmac_signature():
    secret = "test_secret_key"
    ts = int(time.time())
    body = b"{\"id\":\"evt_123\",\"amount\":5000}"
    signed_payload = f"{ts}.".encode() + body
    sig = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    header = f"t={ts},v1={sig}"
    
    assert verify_hmac_signature(body, header, secret) is True
    assert verify_hmac_signature(body, "t=1,v1=wrong", secret) is False

def test_webhook_deduplication():
    router = WebhookRouter()
    res1 = router.process_event("evt_01", "stripe", {"type": "payment_intent.succeeded"})
    assert res1["status"] == "processed"
    res2 = router.process_event("evt_01", "stripe", {"type": "payment_intent.succeeded"})
    assert res2["status"] == "duplicate"

def test_ledger_balanced_transaction():
    engine = LedgerEngine()
    tx = Transaction(
        transaction_id="tx_100",
        description="Customer Payment",
        entries=[
            JournalEntry("cash_escrow", 5000, "DEBIT"),
            JournalEntry("customer_balance", 5000, "CREDIT")
        ]
    )
    assert engine.record_transaction(tx) is True
