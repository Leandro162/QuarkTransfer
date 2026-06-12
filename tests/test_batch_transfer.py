import unittest
from unittest.mock import patch

import server
from quark_transfer import QuarkError


class ParseCsvRowsTests(unittest.TestCase):
    def test_parses_chinese_columns_and_ignores_empty_rows(self):
        rows = server.parse_csv_rows(
            "\ufeff文件名称,夸克链接,提取码\n"
            "资源一,https://pan.quark.cn/s/abc123,9xyz\n"
            ",,\n"
        )

        self.assertEqual(
            rows,
            [
                {
                    "row_number": 2,
                    "share_title": "资源一",
                    "url": "https://pan.quark.cn/s/abc123",
                    "passcode": "9xyz",
                }
            ],
        )

    def test_accepts_common_aliases(self):
        rows = server.parse_csv_rows(
            "title,URL,pwd\n"
            "Alias item,https://pan.quark.cn/s/alias,1234\n"
        )

        self.assertEqual(rows[0]["share_title"], "Alias item")
        self.assertEqual(rows[0]["url"], "https://pan.quark.cn/s/alias")
        self.assertEqual(rows[0]["passcode"], "1234")

    def test_rejects_csv_without_a_url_column(self):
        with self.assertRaisesRegex(ValueError, "链接列"):
            server.parse_csv_rows("文件名称,提取码\n资源一,1234\n")

    def test_rejects_more_than_one_hundred_valid_rows(self):
        csv_text = "文件名称,夸克链接\n" + "\n".join(
            f"资源{index},https://pan.quark.cn/s/{index}"
            for index in range(101)
        )

        with self.assertRaisesRegex(ValueError, "100"):
            server.parse_csv_rows(csv_text)


class TransferBatchTests(unittest.TestCase):
    @patch("server.transfer")
    def test_processes_rows_in_order_and_keeps_going_after_failure(self, transfer_mock):
        transfer_mock.side_effect = [
            {
                "ok": True,
                "title": "资源一",
                "share_url": "https://pan.quark.cn/s/new1",
                "short_url": "https://s.panlays.com/one",
                "feishu": {"ok": True},
            },
            QuarkError("第二行失败"),
            {
                "ok": True,
                "title": "资源三",
                "share_url": "https://pan.quark.cn/s/new3",
                "short_url": "https://s.panlays.com/three",
                "feishu": {"ok": True},
            },
        ]

        result = server.transfer_batch(
            {
                "csv_text": (
                    "文件名称,夸克链接,提取码\n"
                    "资源一,https://pan.quark.cn/s/one,1111\n"
                    "资源二,https://pan.quark.cn/s/two,2222\n"
                    "资源三,https://pan.quark.cn/s/three,3333\n"
                ),
                "cookie": "cookie-value",
                "target_fid": "target-folder",
                "auto_shortlink": True,
            }
        )

        self.assertEqual(result["total"], 3)
        self.assertEqual(result["succeeded"], 2)
        self.assertEqual(result["failed"], 1)
        self.assertEqual([item["row_number"] for item in result["results"]], [2, 4])
        self.assertEqual(result["errors"][0]["row_number"], 3)
        self.assertEqual(transfer_mock.call_count, 3)
        self.assertEqual(
            transfer_mock.call_args_list[0].args[0],
            {
                "url": "https://pan.quark.cn/s/one",
                "passcode": "1111",
                "share_title": "资源一",
                "cookie": "cookie-value",
                "target_fid": "target-folder",
                "auto_shortlink": True,
            },
        )


if __name__ == "__main__":
    unittest.main()
