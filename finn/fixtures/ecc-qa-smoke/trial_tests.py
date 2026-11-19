import importlib, os, unittest
policy = importlib.import_module(os.environ["TRIAL_VARIANT"])
class SyntheticPolicyTests(unittest.TestCase):
    def test_member_cannot_approve(self):
        self.assertEqual(policy.approve(role="member",can_review=False,bank_match=True), "forbidden")
    def test_admin_without_permission_cannot_approve(self):
        self.assertEqual(policy.approve(role="admin",can_review=False,bank_match=True), "forbidden")
    def test_receipt_without_bank_match_cannot_approve(self):
        self.assertEqual(policy.approve(role="super_admin",can_review=True,bank_match=False), "unmatched")
    def test_authorized_match_and_repeat(self):
        self.assertEqual(policy.approve(role="super_admin",can_review=True,bank_match=True), "approved")
        self.assertEqual(policy.approve(role="super_admin",can_review=True,bank_match=True,already_approved=True), "already_approved")
if __name__ == "__main__": unittest.main()
