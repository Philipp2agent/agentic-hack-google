from paypulse.config import settings
from paypulse.webhooks import WebhookRouter
from paypulse.ledger import LedgerEngine

def create_app():
    router = WebhookRouter()
    ledger = LedgerEngine()
    return {"router": router, "ledger": ledger, "settings": settings}

if __name__ == "__main__":
    app = create_app()
    print(f"PayPulse initialized in {app['settings'].environment} mode.")
