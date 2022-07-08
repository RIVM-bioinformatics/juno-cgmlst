from Bio import SeqIO
import pandas as pd
import pathlib
from sys import path
import unittest

main_script_path = str(
    pathlib.Path(pathlib.Path(__file__).parent.absolute()).parent.absolute()
)
path.insert(0, main_script_path)
from bin import get_allele_hashes


class TestCgmlstHasher(unittest.TestCase):
    def test_allele_hashing(self):
        allele = get_allele_hashes.Allele(seq="ACTGACTGACTG")
        allele.update_hash()
        expected_output = "fdfc2bd20f914826b284ce70cfb09e8343d8bba2"
        self.assertEqual(allele.hash, expected_output)

    def test_hash_for_allele_number_is_found(self):
        with open("tests/example_input/locusx.fasta") as file_:
            parsed_fasta = SeqIO.parse(file_, "fasta")
            fasta_record = next(parsed_fasta)
        allele = get_allele_hashes.Allele(fasta_record=fasta_record)
        allele.extract_attr_from_fasta_record()
        expected_output = "73d83c30aac82425db66e6f074b3278c5ec01404"
        self.assertEqual(allele.hash, expected_output)

    def test_locus_get_subset_alleles(self):
        locus = get_allele_hashes.Locus(fasta_file="tests/example_input/locusx.fasta")
        locus.get_locus_name_from_fasta_file()
        locus.get_subset_alleles_from_fasta(id_numbers=[1, 3])
        hash_tbl = locus.make_table_with_hashes(subset=True)
        expected_output = pd.DataFrame.from_dict(
            {
                "id_number": [1, 3],
                "hash": [
                    "73d83c30aac82425db66e6f074b3278c5ec01404",
                    "0273d1c3e65880eacb77e0e9385e7e51c0bdfe9c",
                ],
            }
        )
        self.assertTrue(isinstance(locus.alleles["locusx_1"], get_allele_hashes.Allele))
        self.assertTrue(len(locus.alleles), 2)
        self.assertTrue("locusx_3" in locus.alleles.keys())
        self.assertTrue(all(hash_tbl == expected_output))

    def test_locus_get_all_alleles(self):
        locus = get_allele_hashes.Locus(fasta_file="tests/example_input/locusx.fasta")
        locus.get_locus_name_from_fasta_file()
        locus.get_all_alleles_from_fasta()
        hash_tbl = locus.make_table_with_hashes()
        expected_output = pd.DataFrame.from_dict(
            {
                "id_number": [1, 2, 3, 4, 5],
                "hash": [
                    "73d83c30aac82425db66e6f074b3278c5ec01404",
                    "8e049af5c551058534b88b9dbddbd56d521a6372",
                    "0273d1c3e65880eacb77e0e9385e7e51c0bdfe9c",
                    "627ede0f675b9236075a32e0958493d7519181d0",
                    "0535a35b12c4f532fba151d686b1c2ba41b47024",
                ],
            }
        )
        self.assertTrue(isinstance(locus.alleles["locusx_1"], get_allele_hashes.Allele))
        self.assertTrue(len(locus.alleles), 5)
        self.assertTrue("locusx_2" in locus.alleles.keys())
        self.assertTrue("locusx_3" in locus.alleles.keys())
        self.assertTrue("locusx_4" in locus.alleles.keys())
        self.assertTrue("locusx_5" in locus.alleles.keys())
        self.assertTrue(all(hash_tbl == expected_output))

    @unittest.skipIf(
        not pathlib.Path("/mnt/db/juno/cgmlst/prepared_schemes").exists(),
        "Skipped in non-RIVM environments because database is not present",
    )
    def test_translate_chewbbaca_report_to_hashes(self):
        expected_output = pd.read_csv(
            "tests/example_output/expected_result_chewbbaca_to_hashes.tsv",
            sep="\t",
            index_col=0,
        )
        sample2_hashes = get_allele_hashes.CgmlstResult(
            chewbbaca_result_file="tests/example_output/example_result_chewbbaca.tsv",
            scheme_name="shigella",
        )
        hashed_report = sample2_hashes.get_hashed_cgmlst_report()
        self.assertTrue(all(hashed_report == expected_output))


if __name__ == "__main__":
    unittest.main()
