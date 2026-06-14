import unittest

import server


class LocalTokenTests(unittest.TestCase):
    def test_protects_all_mutating_api_routes(self):
        self.assertTrue(server.requires_local_token("/api/transfer"))
        self.assertTrue(server.requires_local_token("/api/transfer/batch"))
        self.assertTrue(server.requires_local_token("/api/tracker/links"))

    def test_rejects_missing_or_wrong_token(self):
        self.assertFalse(server.valid_local_token("", "expected-token"))
        self.assertFalse(server.valid_local_token("wrong-token", "expected-token"))
        self.assertTrue(server.valid_local_token("expected-token", "expected-token"))

    def test_shutdown_route_is_not_supported(self):
        self.assertFalse(server.is_supported_post_path("/api/shutdown"))

    def test_service_only_accepts_loopback_hosts(self):
        self.assertTrue(server.is_loopback_host("127.0.0.1"))
        self.assertTrue(server.is_loopback_host("localhost"))
        self.assertFalse(server.is_loopback_host("0.0.0.0"))
        self.assertFalse(server.is_loopback_host("192.168.1.10"))


if __name__ == "__main__":
    unittest.main()
