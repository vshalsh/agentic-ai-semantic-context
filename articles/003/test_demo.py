import unittest
from issuer import Issuer
from server import Runtime

class RuntimeTests(unittest.TestCase):
    def test_execution_retry_and_stop(self):
        issuer = Issuer()
        runtime = Runtime(issuer)
        token = issuer.issue("t", "acme", "invoice.approve", "INV-1")
        args = dict(token=token, task_id="t", tenant="acme",
                    action="invoice.approve", resource="INV-1", request_id="1")
        self.assertTrue(runtime.execute(**args)["ok"])
        self.assertTrue(runtime.execute(**args)["ok"])
        self.assertEqual(len(runtime.audit), 1)
        runtime.stop("t")
        self.assertEqual(runtime.execute(**{**args, "request_id": "2"})["reason"], "task_stopped")

    def test_revocation(self):
        issuer = Issuer()
        runtime = Runtime(issuer)
        token = issuer.issue("t", "acme", "invoice.approve", "INV-1")
        issuer.revoke(token)
        self.assertEqual(runtime.execute(token=token, task_id="t", tenant="acme",
            action="invoice.approve", resource="INV-1", request_id="1")["reason"], "capability_denied")

if __name__ == "__main__":
    unittest.main()
