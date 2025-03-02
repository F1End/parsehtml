import unittest

from src import loss_parser


class TestOrxyLossParser(unittest.TestCase):

    def setUp(self):
        self.testparser = loss_parser.OryxLossParser()

    def test_default_init(self):
        test_oryxparser = loss_parser.OryxLossParser()

        self.assertEqual(test_oryxparser.category_counter, 0)
        self.assertEqual(test_oryxparser.category_name, None)
        self.assertEqual(test_oryxparser.category_summary, None)
        self.assertEqual(test_oryxparser.type_name, None)
        self.assertEqual(test_oryxparser.type_ttl_count, 0)
        self.assertEqual(test_oryxparser.type_img_links, None)
        self.assertEqual(test_oryxparser.errors,[])


if __name__ == '__main__':
    unittest.main()
