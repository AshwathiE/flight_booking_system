import uuid
class PaymentGateway:
    def process(self, payment_id: str, amount: float, currency: str, method: str) -> dict:
        raise NotImplementedError()

    def refund(self, transaction_id: str, amount: float, reason: str) -> dict:
        raise NotImplementedError()
class MockPaymentGateway(PaymentGateway):
    def __init__(self, default_outcome: str = "SUCCESS", refund_outcome: str = "REFUND_SUCCESS"):
        self.default_outcome = default_outcome
        self.refund_outcome = refund_outcome

    def process(self, payment_id: str, amount: float, currency: str, method: str) -> dict:
        # Deterministic outcome can be driven by method or default_outcome
        method_upper = method.upper()
        if "FAIL" in method_upper or self.default_outcome == "FAILED":
            return {
                "status": "FAILED",
                "transaction_id": None,
                "failure_reason": "Mock payment failure"
            }
        elif "TIMEOUT" in method_upper or self.default_outcome == "TIMEOUT":
            return {
                "status": "TIMEOUT",
                "transaction_id": None,
                "failure_reason": "Mock payment timeout"
            }
        else:
            return {
                "status": "SUCCESS",
                "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
                "failure_reason": None
            }
    def refund(self, transaction_id: str, amount: float, reason: str) -> dict:
        reason_upper = reason.upper()
        if "FAIL" in reason_upper or self.refund_outcome == "REFUND_FAILED":
            return {
                "status": "REFUND_FAILED",
                "refund_id": None,
                "failure_reason": "Mock refund failed"
            }
        else:
            return {
                "status": "SUCCESS",
                "refund_id": f"ref_{uuid.uuid4().hex[:12]}",
                "failure_reason": None
            }
