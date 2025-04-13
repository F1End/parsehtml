from unittest import TestCase, main
from unittest.mock import MagicMock, patch, call
from src import loss_parser


class TestOrxyLossParser(TestCase):

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
        self.assertEqual(test_oryxparser.errors, [])

    @patch('src.loss_parser.BeautifulSoup')
    @patch('src.loss_parser.OryxLossParser._parse_tag_data')
    def test_parse_losses(self, mock_parse_tagdata, mock_bs):
        bs_instance = MagicMock()
        mock_bs.return_value = bs_instance
        fake_tags = ["tag1", "tag2", "tag3"]
        bs_instance.find_all.return_value = fake_tags
        fake_content = "Some html content"
        exected_findall_call = ["h3", "h2", "li"]
        expected_calls = [call(fake_tags[0], []), call(fake_tags[1], []),
                          call(fake_tags[2], [])]

        # Case 1: Normal, tags returned
        result = self.testparser.parse_losses(fake_content)
        self.assertEqual(result, [])  # mocking parse_tag_data -> list won't update
        mock_bs.assert_called_with(fake_content, "html.parser")
        bs_instance.find_all.assert_called_with(exected_findall_call)
        mock_parse_tagdata.assert_has_calls(expected_calls)

        mock_parse_tagdata.reset_mock()
        mock_bs.reset_mock()
        bs_instance.reset_mock()

        # Case 2: no tags found
        bs_instance.find_all.return_value = []
        result = self.testparser.parse_losses(fake_content)
        self.assertEqual(result, [])  # mocking parse_tag_data -> list won't update
        mock_bs.assert_called_with(fake_content, "html.parser")
        bs_instance.find_all.assert_called_with(exected_findall_call)
        mock_parse_tagdata.assert_not_called()

    @patch('src.loss_parser.BeautifulSoup')
    @patch('src.loss_parser.OryxLossParser._find_str_pos')
    def test_truncate_content(self, find_str_mock, mock_bs):
        bs_instance = MagicMock()
        mock_bs.return_value = bs_instance
        fake_tags = ["tag1", "tag2", "tag3"]
        bs_instance.find_all.return_value = fake_tags
        fake_content = "Some html content"
        bs_instance.__str__.return_value = fake_content
        exclude = "content"
        mocked_pos_return = 10
        find_str_mock.return_value = mocked_pos_return

        # Case 1: tag name is provided
        truncated = self.testparser.truncate_content(
            fake_content, exclude, tag_name="a")
        self.assertEqual(truncated, fake_content[:10])
        mock_bs.assert_called_with(fake_content, "html.parser")
        bs_instance.find_all.assert_called_with("a")
        find_str_mock.assert_called_with(fake_tags,
                                         exclude,
                                         fake_content)

        find_str_mock.reset_mock()
        mock_bs.reset_mock()
        bs_instance.reset_mock()

        # Case 2: tag name NOT provided
        truncated_2 = self.testparser.truncate_content(
            fake_content, exclude)
        self.assertEqual(truncated_2, fake_content[:10])
        mock_bs.assert_called_with(fake_content, "html.parser")
        bs_instance.find_all.assert_called_with()
        find_str_mock.assert_called_with(fake_tags,
                                         exclude,
                                         fake_content)

    def test__find_str_pos(self):
        tag1, tag2, tag3 = MagicMock(), MagicMock(), MagicMock()
        tags = [tag1, tag2, tag3]
        tag1.get_text.return_value = "not here"
        tag2.get_text.return_value = "content here"
        tag3.get_text.return_value = "not here"
        tag2.__str__.return_value = "content"
        content_str = "Some html content"
        find_str = "content"

        # Case 1: string found
        result = self.testparser._find_str_pos(tags, find_str, content_str)
        self.assertEqual(result, 10)
        tag1.get_text.assert_called_once()
        tag2.get_text.assert_called_once()
        tag3.get_text.assert_not_called()
        tag2.__str__.assert_called_once()

        tag1.reset_mock()
        tag2.reset_mock()
        tag3.reset_mock()

        # Case 2: string not found -> Exception
        tag2.get_text.return_value = "not even here now"
        with self.assertRaises(Exception) as e:
            result = self.testparser._find_str_pos(tags, find_str, content_str)
        tag1.get_text.assert_called_once()
        tag2.get_text.assert_called_once()
        tag3.get_text.assert_called_once()
        tag1.__str__.assert_not_called()
        tag2.__str__.assert_not_called()
        tag3.__str__.assert_not_called()

    @patch('src.loss_parser.OryxLossParser._update_category')
    def test_parse_category(self, update_cat_mock):
        mock_tag = MagicMock()

        # Case 1: tag is h3 AND new category
        mock_tag.name = "h3"
        tag_instance = MagicMock()
        mock_tag.find.return_value = tag_instance
        found_category_name = "Some value"
        tag_instance.get_text.return_value = found_category_name
        self.testparser._parse_category(mock_tag)
        mock_tag.find.assert_called_with("span", class_="mw-headline")
        update_cat_mock.assert_called_with(mock_tag, found_category_name)
        tag_instance.get_text.assert_called_with()

        mock_tag.reset_mock()
        update_cat_mock.reset_mock()

        # Case 2: tag is h3 but NOT new category
        mock_tag.name = "h3"
        mock_tag.find.return_value = None
        self.testparser._parse_category(mock_tag)
        mock_tag.find.assert_called_with("span", class_="mw-headline")
        update_cat_mock.assert_not_called()

        mock_tag.reset_mock()
        update_cat_mock.reset_mock()

        # Case 3: tag is NOT h3
        mock_tag.name = "img"
        mock_tag.find.return_value = None
        self.testparser._parse_category(mock_tag)
        mock_tag.find.assert_not_called()
        update_cat_mock.assert_not_called()

        mock_tag.reset_mock()
        update_cat_mock.reset_mock()

    @patch('src.loss_parser.OryxLossParser._parse_category_summary')
    def test__update_category(self, parse_cat_summ_mock):
        tag = "Some tag"
        new_cat = "IFV"
        self.testparser.category_counter = 0
        self.testparser.category_name = "Tanks"
        summary_val = "Category summary values"
        parse_cat_summ_mock.return_value = summary_val

        self.testparser._update_category(tag, new_cat)
        self.assertEqual(self.testparser.category_counter, 1)
        self.assertEqual(self.testparser.category_name, new_cat)
        self.assertEqual(self.testparser.category_summary, summary_val)
        parse_cat_summ_mock.assert_called_with(tag, new_cat)

    def test__parse_category_summary(self):
        tag = MagicMock()
        mock_text = "IFVs:(5 destroyed, 10 damaged)"
        tag.get_text.return_value = mock_text
        new_cat_name = "IFVs:"
        expected = "5 destroyed, 10 damaged"

        summary = self.testparser._parse_category_summary(tag, new_cat_name)
        self.assertEqual(summary, expected)
        tag.get_text.assert_called_with()

    @patch('src.loss_parser.OryxLossParser._parse_type_count')
    @patch('src.loss_parser.OryxLossParser._parse_type_images')
    def test__parse_type(self, mock_type_img, mock_type_count):
        tag = MagicMock()
        text = "33 T-64BV: (blah, blah) "
        tag.get_text.return_value = text
        expected_name = "T-64BV"
        mock_words = ["33", "T-64BV"]
        img_link = "some img link"
        mock_type_img.return_value = img_link
        mock_count = 33
        mock_type_count.return_value = mock_count

        # Case 1: category identified (counter > 0) and "li" tag
        tag.name = "li"
        self.testparser.category_counter = 1
        self.testparser._parse_type(tag)
        self.assertEqual(self.testparser.type_ttl_count, mock_count)
        self.assertEqual(self.testparser.type_name, expected_name)
        self.assertEqual(self.testparser.type_img_links, img_link)
        tag.get_text.assert_called_with(strip=True)
        mock_type_count.assert_called_with(mock_words)
        mock_type_img.assert_called_with(tag)

        tag.reset_mock()
        mock_type_count.reset_mock()
        mock_type_img.reset_mock()

        # Case 2: category not yet found
        tag.name = "li"
        self.testparser.category_counter = 0
        self.testparser._parse_type(tag)
        tag.get_text.assert_not_called()
        mock_type_count.assert_not_called()
        mock_type_img.assert_not_called()

        # Case 3: not "li" tag
        tag.name = "h3"
        self.testparser.category_counter = 1
        self.testparser._parse_type(tag)
        tag.get_text.assert_not_called()
        mock_type_count.assert_not_called()
        mock_type_img.assert_not_called()

        # Case 4: Not identifiyed category AND not "li" tag
        tag.name = "h3"
        self.testparser.category_counter = 0
        self.testparser._parse_type(tag)
        tag.get_text.assert_not_called()
        mock_type_count.assert_not_called()
        mock_type_img.assert_not_called()

    def test__parse_type_count(self):
        # Case 1: text includes numeric count
        text = ["33", "T-64BV"]
        expected = 33

        type_count = self.testparser._parse_type_count(text)
        self.assertEqual(type_count, expected)

        # Case 2: Counter is missing convertible value
        text_2 = ["t-64BV"]
        with self.assertRaises(Exception) as e:
            type_count = self.testparser._parse_type_count(text_2)
            self.assertEqual(self.testparser.errors[0], (e, text_2))

    def test__parse_type_image(self):
        tag = MagicMock()
        img_mock1, img_mock2, img_mock3 = MagicMock(), MagicMock(), MagicMock()
        tag_mocks = [img_mock1, img_mock2, img_mock3]
        tag.find_all.return_value = tag_mocks

        # Case 1: single image link
        image_mock = "img_link_here"
        img_mock2.attrs = {"src": image_mock}
        img_mock2.__getitem__.return_value = image_mock

        returned_img = self.testparser._parse_type_images(tag)
        self.assertEqual(returned_img, image_mock)
        img_mock2.__getitem__.assert_called_with("src")
        img_mock1.__getitem__.assert_not_called()
        img_mock3.__getitem__.assert_not_called()

        img_mock1.reset_mock()
        img_mock2.reset_mock()
        img_mock3.reset_mock()

        # Case 2: multiple images
        image_mock = "img_link_here"
        image_mock2 = "another_img_link_here"
        img_mock2.attrs = {"src": image_mock}
        img_mock2.__getitem__.return_value = image_mock
        img_mock3.attrs = {"src": image_mock2}
        img_mock3.__getitem__.return_value = image_mock2
        expected = " ".join([image_mock, image_mock2])

        returned_imges = self.testparser._parse_type_images(tag)
        self.assertEqual(returned_imges, expected)
        img_mock2.__getitem__.assert_called_with("src")
        img_mock1.__getitem__.assert_not_called()
        img_mock3.__getitem__.assert_called_with("src")

        img_mock1.reset_mock()
        img_mock2.reset_mock()
        img_mock3.reset_mock()

        # Case 3: no "src" in img.attrs
        img_mock2.attrs = {"blah": None}
        img_mock3.attrs = {"blah": None}
        expected = None

        returned_img = self.testparser._parse_type_images(tag)
        self.assertEqual(returned_img, expected)
        img_mock2.__getitem__.assert_not_called()
        img_mock1.__getitem__.assert_not_called()
        img_mock3.__getitem__.assert_not_called()

        img_mock1.reset_mock()
        img_mock2.reset_mock()
        img_mock3.reset_mock()

        # Case 4: no "img" tag found
        tag.find_all.return_value = []
        img_mock2.attrs = {"blah": None}
        img_mock3.attrs = {"blah": None}
        expected = None

        returned_img = self.testparser._parse_type_images(tag)
        self.assertEqual(returned_img, expected)

    @patch("src.loss_parser.OryxLossParser._merge_broken_losses")
    def test__parse_loss_item(self, merge_broken_mock):
        # Case 1: valid text value with both brackets ()
        merge_broken_mock.return_value = "(Text value)"
        tag = MagicMock()
        text_value, proof_value = "(Text value)", "Proof link"
        tag.get_text.return_value = text_value
        tag.get.return_value = proof_value

        output = self.testparser._parse_loss_item(tag)
        self.assertEqual(output, (text_value, proof_value))
        tag.get_text.assert_called_with(strip=True)
        tag.get.assert_called_with("href")
        merge_broken_mock.assert_called_with("(Text value)")

        # Case 2: Not valid test value
        merge_broken_mock.return_value = None
        tag = MagicMock()
        text_value, proof_value = "(Text value", "Proof link"
        tag.get_text.return_value = text_value
        tag.get.return_value = proof_value

        output = self.testparser._parse_loss_item(tag)
        self.assertEqual(output, ("skip", "skip"))
        tag.get_text.assert_called_with(strip=True)
        tag.get.assert_called_with("href")
        merge_broken_mock.assert_called_with("(Text value")

    def test__merge_broken_losses(self):
        # Case 1: Text broken into three tags
        consecutive_pieces = ["(1 ", "and 2", " damaged)"]
        response = []
        expected_buffer = None
        for piece in consecutive_pieces:
            self.assertEqual(self.testparser.buffer, expected_buffer)
            response.append(self.testparser._merge_broken_losses(piece))
            expected_buffer = piece if not expected_buffer else expected_buffer + piece
        self.assertEqual(self.testparser.buffer, None)
        self.assertEqual(response[0], None)
        self.assertEqual(response[1], None)
        self.assertEqual(response[2], "(1 and 2 damaged)")

        # Case 2: Text is not broken -> return same text
        good_text = ("(1, destroyed)")
        response = self.testparser._merge_broken_losses(good_text)
        self.assertEqual(good_text, response)
        self.assertEqual(self.testparser.buffer, None)

    def test__create_longrow(self):
        self.testparser.category_counter = 1
        self.testparser.category_name = "Tank"
        self.testparser.category_summary = "54 destroyed, 66 damaged"
        self.testparser.type_name = "T-64BV"
        self.testparser.type_ttl_count = 33
        self.testparser.type_img_links = "some link here"
        item = "destoyed"
        proof = "img_link_here"
        expected_dict = {"category_counter": self.testparser.category_counter,
                         "category_name": self.testparser.category_name,
                         "category_summary": self.testparser.category_summary,
                         "type_name": self.testparser.type_name,
                         "type_ttl_count": self.testparser.type_ttl_count,
                         "type_img_links": self.testparser.type_img_links,
                         "loss_item": item,
                         "loss_proof": proof}
        result = self.testparser._create_longrow(item, proof)
        self.assertEqual(result, expected_dict)

    @patch('src.loss_parser.OryxLossParser._parse_loss_item')
    @patch('src.loss_parser.OryxLossParser._create_longrow')
    def test__self_add_losses(self, mock_longrow, mock_parse_loss):
        tag = MagicMock()
        item1, item2, item3 = ["item1", "item2", "item3"]
        items = [item1, item2, item3]
        tag.find_all.return_value = items
        parse_return_vals = [("loss1", "link1"),
                             ("loss2", "link2"),
                             ("loss3", "link3")]
        mock_parse_loss.side_effect = parse_return_vals
        longrows = ["row1", "row2", "row3"]
        mock_longrow.side_effect = longrows

        # Case 1: Category found (counter > 0) and tag is "li"
        expected_parse_calls = [call(item1), call(item2), call(item3)]
        expected_create_longrow_calls = [call(*parse_return_vals[0]),
                                         call(*parse_return_vals[1]),
                                         call(*parse_return_vals[2])]
        loss_list = []
        self.testparser.category_counter = 1
        tag.name = "li"
        self.testparser._add_losses(tag, loss_list)
        self.assertEqual(loss_list, longrows)
        tag.find_all.assert_called_with("a")
        mock_parse_loss.assert_has_calls(expected_parse_calls)
        mock_longrow.assert_has_calls(expected_create_longrow_calls)

        mock_parse_loss.reset_mock()
        mock_longrow.reset_mock()
        tag.reset_mock()

        # Case 2: Category is not found
        loss_list_2 = []
        tag.name = "li"
        self.testparser.category_counter = 0
        self.testparser._add_losses(tag, loss_list)
        self.assertEqual(loss_list_2, [])
        tag.find_all.assert_not_called()
        mock_parse_loss.assert_not_called()
        mock_longrow.assert_not_called()

        # Case 3: Not "li" tag
        loss_list_2 = []
        tag.name = "h3"
        self.testparser.category_counter = 1
        self.testparser._add_losses(tag, loss_list)
        self.assertEqual(loss_list_2, [])
        tag.find_all.assert_not_called()
        mock_parse_loss.assert_not_called()
        mock_longrow.assert_not_called()

        # Case 4: Neither
        loss_list_2 = []
        tag.name = "h3"
        self.testparser.category_counter = 0
        self.testparser._add_losses(tag, loss_list)
        self.assertEqual(loss_list_2, [])
        tag.find_all.assert_not_called()
        mock_parse_loss.assert_not_called()
        mock_longrow.assert_not_called()


if __name__ == '__main__':
    main()
