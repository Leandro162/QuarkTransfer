import unittest
from pathlib import Path


class CsvUploadUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = Path("web/index.html").read_text(encoding="utf-8")

    def test_upload_box_has_loading_success_and_error_states(self):
        for marker in (
            'id="csvUploadBox"',
            'id="csvUploadIcon"',
            'id="csvUploadTitle"',
            'id="csvUploadDetail"',
            'class="upload-spinner"',
            'classList.add(state)',
        ):
            self.assertIn(marker, self.html)

    def test_selected_file_can_be_replaced_or_removed(self):
        self.assertIn('id="replaceCsv"', self.html)
        self.assertIn('id="removeCsv"', self.html)
        self.assertIn("resetCsvUpload", self.html)


if __name__ == "__main__":
    unittest.main()
