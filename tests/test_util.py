from unittest import TestCase, main
from unittest.mock import MagicMock, patch, call
from pathlib import Path
import sys

import pandas as pd

from src import util


class TestHTMLFileContent(TestCase):

    def setUp(self):
        fake_path = "some/path/to/file.html"
        self.test_htmlfcont = util.HTMLFileContent(fake_path)

    @patch.object(util.Content, "__init__", return_value=None)
    def test_init(self, content_mock):
        some_source = "path/to/some/file.html"
        test_instance = util.HTMLFileContent(some_source)
        content_mock.assert_called_with(some_source)
        self.assertEqual(test_instance.soup, None)

    @patch("src.util.open")
    @patch("src.util.BeautifulSoup")
    def test_load(self, bs_mock, open_mock):
        file_mock = MagicMock()
        fake_html = "some html content"
        file_mock.read.return_value = fake_html
        open_mock.return_value.__enter__.return_value = file_mock
        some_source = "path/to/some/file.html"
        test_instance = util.HTMLFileContent(some_source).load()
        open_mock.assert_called_with(some_source)
        bs_mock.assert_called_with(fake_html, "html.parser")
        self.assertEqual(test_instance._content, fake_html)

    @patch("src.util.HTMLFileContent._find_str_pos")
    def test_truncate_content(self, find_str_mock):
        soup_mock = MagicMock()
        content_str = "Some html content"
        fake_tags = ["tag1", "tag2", "tag3"]
        soup_mock.find_all.return_value = fake_tags
        fake_content = "Some html content"
        soup_mock.__str__.return_value = fake_content
        exclude = "content"
        mocked_pos_return = 10
        find_str_mock.return_value = mocked_pos_return
        self.test_htmlfcont.soup = soup_mock
        self.test_htmlfcont._content = content_str

        # Case 1: tag name is provided
        truncated = self.test_htmlfcont.truncate_content(exclude, tag_name="a")
        self.assertEqual(self.test_htmlfcont._content, content_str[:10])
        soup_mock.find_all.assert_called_with("a")
        find_str_mock.assert_called_with(fake_tags, exclude)

        find_str_mock.reset_mock()

        # Case 2: tag name NOT provided
        truncated_2 = self.test_htmlfcont.truncate_content(exclude)
        self.assertEqual(self.test_htmlfcont._content, fake_content[:10])
        soup_mock.find_all.assert_called_with()
        find_str_mock.assert_called_with(fake_tags, exclude)

    def test__find_str_pos(self):
        soup_mock = MagicMock()
        content_str = "Some html content"
        soup_mock.__str__.return_value = content_str
        self.test_htmlfcont.soup = soup_mock
        tag1, tag2, tag3 = MagicMock(), MagicMock(), MagicMock()
        tags = [tag1, tag2, tag3]
        tag1.get_text.return_value = "not here"
        tag2.get_text.return_value = "content here"
        tag3.get_text.return_value = "not here"
        tag2.__str__.return_value = "content"
        find_str = "content"

        # Case 1: string found
        result = self.test_htmlfcont._find_str_pos(tags, find_str)
        self.assertEqual(result, 10)
        tag1.get_text.assert_called_once()
        tag2.get_text.assert_called_once()
        tag3.get_text.assert_not_called()
        tag2.__str__.assert_any_call()

        tag1.reset_mock()
        tag2.reset_mock()
        tag3.reset_mock()

        # Case 2: string not found -> Exception
        tag2.get_text.return_value = "not even here now"
        with self.assertRaises(Exception) as e:
            result = self.test_htmlfcont._find_str_pos(tags, find_str)
        tag1.get_text.assert_called_once()
        tag2.get_text.assert_called_once()
        tag3.get_text.assert_called_once()
        tag1.__str__.assert_not_called()
        tag2.__str__.assert_not_called()
        tag3.__str__.assert_not_called()


class TestParsedContent(TestCase):

    @patch.object(util.Content, "__init__", return_value=None)
    def test_init(self, content_mock):
        some_source = [{"blah": "test"}]
        test_instance = util.ParsedContent(some_source)
        content_mock.assert_called_with(some_source)

    @patch("src.util.pd")
    def test_load(self, pandas_mock):
        fake_df = "some dataframe"
        pandas_mock.DataFrame.return_value = fake_df
        pandas_mock.read_csv.return_value = fake_df

        # Case 1: content is list[dict] (passed in parsing workflow)
        some_source = [{"blah": "test"}]
        test_instance = util.ParsedContent(some_source).load()
        pandas_mock.DataFrame.assert_called_with(some_source)
        self.assertEqual(test_instance._content, fake_df)
        pandas_mock.reset()

        # Case 2: content is Path or str (reading in file directly)
        path_file_source = Path("path", "to", "some.csv")
        test_instance = util.ParsedContent(path_file_source).load()
        pandas_mock.read_csv.assert_called_with(path_file_source)
        self.assertEqual(test_instance._content, fake_df)
        pandas_mock.reset()

        # Case 3: content is str (reading in file directly)
        str_ile_source = "path/to/some/file.csv"
        test_instance = util.ParsedContent(str_ile_source).load()
        pandas_mock.read_csv.assert_called_with(str_ile_source)
        self.assertEqual(test_instance._content, fake_df)
        pandas_mock.reset()

        # Case 3: wrong input content
        wrong_source = 12345
        with self.assertRaises(TypeError) as context:
            test_instance = util.ParsedContent(wrong_source).load()

    @patch("src.util.pd")
    def test_clean_content(self, pandas_mock):
        some_source = [{"blah": "test\u00A0"}]
        test_df = pd.DataFrame(some_source)
        pandas_mock.DataFrame.return_value = test_df
        test_instance = util.ParsedContent(some_source).load().clean_content()
        expected = pd.DataFrame([{"blah": "test "}])
        pd.testing.assert_frame_equal(test_instance._content, expected)

    @patch("src.util.pd")
    def test_strip_archive_url(self, pandas_mock):
        some_source = [{"colnamehere": "https://web.archive.org/web/20220424191550/https://postimg.cc/G9jSKh34"}]
        test_df = pd.DataFrame(some_source)
        expected = pd.DataFrame([{"colnamehere": "https://postimg.cc/G9jSKh34"}])
        pandas_mock.DataFrame.return_value = test_df
        test_instance = util.ParsedContent(some_source).load().strip_archive_url()
        pd.testing.assert_frame_equal(test_instance._content, expected)

    @patch("src.util.pd.DataFrame")
    def test_to_csv(self, df_mock):
        df_instance = MagicMock()
        df_mock.return_value = df_instance
        some_source = [{"blah": "test"}]
        output_name = "some_csv"
        test_instance = util.ParsedContent(some_source).load()
        test_instance.to_csv(output_name)
        df_instance.to_csv.assert_called_with(output_name)
        self.assertEqual(test_instance._content, df_instance)


class TestParseArgs(TestCase):

    # Case 1: both arguments provided
    @patch.object(
        sys,
        "argv",
        ["parsehtml", "--file", "input.html", "--output_file", "output.html"],
    )
    def test_args_with_file_and_output_file(self):
        args = util.parse_args()
        self.assertEqual(args.file, "input.html")
        self.assertEqual(args.output_file, "output.html")

    # Case 2: only input file is provided
    @patch.object(sys, "argv", ["parsehtml", "--file", "input.html"])
    def test_args_with_only_file(self):
        with self.assertRaises(SystemExit):
            util.parse_args()

    # Case 3: only output file is provided
    @patch.object(sys, "argv", ["parsehtml", "--output_file", "output.html"])
    def test_args_with_only_output_file(self):
        with self.assertRaises(SystemExit):
            util.parse_args()

    # Case 4: No arguments provided
    @patch.object(sys, "argv", ["parsehtml"])
    def test_args_with_no_arguments(self):
        with self.assertRaises(SystemExit):
            util.parse_args()


if __name__ == "__main__":
    main()
