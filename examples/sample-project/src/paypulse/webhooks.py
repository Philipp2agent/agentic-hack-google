import hmac
import hashlib
import time
from typing import Dict, Any, Optional

def verify_hmac_signature(payload: bytes, signature: str, secret: str, tolerance_seconds: int = 300) -> bool:
    """Verify webhook HMAC SHA256 signature with replay window protection."""
    if not signature or not secret:
        return False
    try:
        parts = dict(item.split("=", 1) for item in signature.split(","))
        ts = int(parts.get("t", 0))
        expected_sig = parts.get("v1", "")
        
        # Check tolerance window if timestamp present
        if ts > 0 and abs(time.time() - ts) > tolerance_seconds:
            return False
            
        signed_payload = f"{ts}.".encode() + payload if ts > 0 else payload
        computed = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed, expected_sig)
    except Exception:
        return False

class WebhookRouter:
    def __init__(self):
        self.processed_ids = set()
        self.dead_letter_queue = []

    def process_event(self, event_id: str, provider: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if event_id in self.processed_ids:
            return {"status": "duplicate", "event_id": event_id, "action": "ignored"}
            
        self.processed_ids.add(event_id)
        return {
            "status": "processed",
            "event_id": event_id,
            "provider": provider,
            "type": data.get("type", "unknown")
        }

    def record_dlq(self, raw_payload: str, reason: str):
        self.dead_letter_queue.append({"payload": raw_payload, "reason": reason, "timestamp": time.time()})
