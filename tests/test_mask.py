import tempfile
import unittest
from pathlib import Path

from scripts.mask import main, mask, mask_with_counts


class MaskTests(unittest.TestCase):
    def test_brazilian_ids_formatted_and_plain(self):
        self.assertEqual(mask("CPF 123.456.789-09 e 12345678909"), "CPF [CPF] e [CPF]")
        self.assertEqual(mask("CNPJ 12.345.678/0001-95 e 12345678000195"), "CNPJ [CNPJ] e [CNPJ]")

    def test_email_and_ip(self):
        self.assertEqual(mask("de joao.silva@empresa.com.br via 10.0.0.15"), "de [EMAIL] via [IP]")

    def test_secrets_in_several_shapes(self):
        self.assertEqual(mask("senha=abc123 token: xyz"), "senha=[SECRET] token: [SECRET]")
        self.assertEqual(mask("Server=db;User Id=sa;Password=Sup3r;"), "Server=db;User Id=sa;Password=[SECRET];")
        self.assertEqual(mask("api_key = k-99"), "api_key = [SECRET]")

    def test_user_folder_and_invoice_key(self):
        self.assertEqual(mask(r"C:\Users\Maria\AppData\x.log"), r"C:\Users\[USER]\AppData\x.log")
        self.assertEqual(mask("chave " + "3" * 44), "chave [NFE-KEY]")

    def test_useful_diagnostic_text_is_kept(self):
        line = "Erro 539 ao emitir NF-e na filial 04 às 14:32, versão 2.4.3, código 0x80070005"
        self.assertEqual(mask(line), line)

    def test_idempotent_and_counts(self):
        text = "a@b.co 10.0.0.1 senha=x"
        once = mask(text)
        self.assertEqual(mask(once), once)
        _, counts = mask_with_counts(text)
        self.assertEqual(counts, {"EMAIL": 1, "IP": 1, "SECRET": 1})

    def test_cli_writes_masked_copy_and_leaves_the_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, out = Path(tmp) / "log.txt", Path(tmp) / "log.masked.txt"
            source.write_text("falha de joao@x.com\n", encoding="utf-8")
            self.assertEqual(main(["mask.py", str(source), "--out", str(out)]), 0)
            self.assertEqual(out.read_text(encoding="utf-8"), "falha de [EMAIL]\n")
            self.assertIn("joao@x.com", source.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
