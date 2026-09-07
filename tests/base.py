from django.test import Client, TestCase


class BaseTestCase(TestCase):
    """
    Base test case for all tests.
    """

    def setUp(self):
        self.client = Client()

    def tearDown(self):
        pass
