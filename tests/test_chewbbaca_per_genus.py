import os
import pathlib
from sys import path
import unittest

main_script_path = str(
    pathlib.Path(pathlib.Path(__file__).parent.absolute()).parent.absolute()
)
path.insert(0, main_script_path)
from bin import chewbbaca_input_files


class TestChewbbacaPerGenus(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.system("mkdir -p test_chewbbaca_per_genus")
        os.system("mkdir -p test_chewbbaca_per_genus/sample1")
        os.system("mkdir -p test_chewbbaca_per_genus/sample2")
        os.system("mkdir -p test_chewbbaca_per_genus/sample3")
        os.system("mkdir -p test_chewbbaca_per_genus/sample4")
        os.system("mkdir -p test_chewbbaca_per_genus/sample5")
        os.system("mkdir -p test_chewbbaca_per_genus/sample6")
        os.system("mkdir -p test_chewbbaca_per_genus/output")

    @classmethod
    def tearDownClass(cls) -> None:
        os.system("rm -rf test_chewbbaca_per_genus")

    def test_dict_with_samples_per_genus(self) -> None:
        """Testing whether the dictionary with samples belonging to a
        genus is created properly for a simple sample
        """
        with open("test_chewbbaca_per_genus/salm_sample_sheet.yaml", "w") as file_:
            file_.write(
                "sample1:\n  assembly: sample1.fasta\n  cgmlst_scheme:\n  - salmonella\n"
            )
        input_chewbbaca = chewbbaca_input_files.inputChewBBACA(
            sample_sheet="test_chewbbaca_per_genus/salm_sample_sheet.yaml",
            output_dir="test_chewbbaca_per_genus/output",
        )
        input_chewbbaca.make_file_with_samples_per_scheme()
        expected_output = {"salmonella": ["sample1.fasta"]}
        actual_output = input_chewbbaca.cgmlst_scheme_dict
        self.assertDictEqual(expected_output, actual_output, actual_output)

    def test_dict_with_samples_per_genus_if_two_cgmlst_schemes_needed(self) -> None:
        """Testing whether the dictionary with samples belonging to a
        genus is created properly for a Listeria and Escherichia, where two
        cgMLST schemes are needed.
        """
        # No need to test Shigella because all Shigella samples have a
        # cgmlst_scheme = escherichia in the sample sheet.
        with open(
            "test_chewbbaca_per_genus/twoschemes_sample_sheet.yaml", "w"
        ) as file_:
            file_.write(
                "sample2:\n  assembly: sample2.fasta\n  cgmlst_scheme:\n  - escherichia\n  - shigella\n"
            )
            file_.write(
                "sample4:\n  assembly: sample4.fasta\n  cgmlst_scheme:\n  - listeria\n  - listeria_optional\n"
            )

        input_chewbbaca = chewbbaca_input_files.inputChewBBACA(
            sample_sheet="test_chewbbaca_per_genus/twoschemes_sample_sheet.yaml",
            output_dir="test_chewbbaca_per_genus/output",
        )
        input_chewbbaca.make_file_with_samples_per_scheme()
        expected_output = {
            "listeria": ["sample4.fasta"],
            "listeria_optional": ["sample4.fasta"],
            "escherichia": ["sample2.fasta"],
            "shigella": ["sample2.fasta"],
        }
        actual_output = input_chewbbaca.cgmlst_scheme_dict
        self.assertDictEqual(expected_output, actual_output, actual_output)

    def test_genus_dict_for_multifiles_multigenera(self) -> None:
        """Testing whether the dictionary with sample files is created properly
        when multiple samples from multiple genera are included
        """
        # No need to test Shigella because all Shigella samples have a
        # cgmlst_scheme = escherichia in the sample sheet.
        with open("test_chewbbaca_per_genus/multi_sample_sheet.yaml", "w") as file_:
            file_.write(
                "sample1:\n  assembly: sample1.fasta\n  cgmlst_scheme:\n  - salmonella\n"
            )
            file_.write(
                "sample2:\n  assembly: sample2.fasta\n  cgmlst_scheme:\n  - salmonella\n"
            )
            file_.write(
                "sample3:\n  assembly: sample3.fasta\n  cgmlst_scheme:\n  - listeria\n  - listeria_optional\n"
            )
            file_.write(
                "sample4:\n  assembly: sample4.fasta\n  cgmlst_scheme:\n  - escherichia\n  - shigella\n"
            )
            file_.write(
                "sample5:\n  assembly: sample5.fasta\n  cgmlst_scheme:\n  - escherichia\n  - shigella\n"
            )

        input_chewbbaca = chewbbaca_input_files.inputChewBBACA(
            sample_sheet="test_chewbbaca_per_genus/multi_sample_sheet.yaml",
            output_dir="test_chewbbaca_per_genus/output",
        )
        input_chewbbaca.make_file_with_samples_per_scheme()
        expected_output = {
            "escherichia": ["sample4.fasta", "sample5.fasta"],
            "listeria": ["sample3.fasta"],
            "listeria_optional": ["sample3.fasta"],
            "salmonella": ["sample1.fasta", "sample2.fasta"],
            "shigella": ["sample4.fasta", "sample5.fasta"],
        }
        actual_output = input_chewbbaca.cgmlst_scheme_dict
        self.assertDictEqual(expected_output, actual_output, actual_output)

    def test_genus_dict_multifiles_multigenera_ignoring_nonsupported(self) -> None:
        """Testing whether the dictionary with sample files is created properly
        when multiple samples from multiple genera are included. However,
        unsupported genera (in this case fakegenus) should be ignored.
        """
        # No need to test Shigella because all Shigella samples have a
        # cgmlst_scheme = escherichia in the sample sheet.
        with open(
            "test_chewbbaca_per_genus/unsupported_sample_sheet.yaml", "w"
        ) as file_:
            file_.write(
                "sample1:\n  assembly: sample1.fasta\n  cgmlst_scheme:\n  - salmonella\n"
            )
            file_.write(
                "sample2:\n  assembly: sample2.fasta\n  cgmlst_scheme:\n  - salmonella\n"
            )
            file_.write(
                "sample3:\n  assembly: sample3.fasta\n  cgmlst_scheme:\n  - listeria\n  - listeria_optional\n"
            )
            file_.write(
                "sample4:\n  assembly: sample4.fasta\n  cgmlst_scheme:\n  - escherichia\n  - shigella\n"
            )
            file_.write(
                "sample5:\n  assembly: sample5.fasta\n  cgmlst_scheme:\n  - escherichia\n  - shigella\n"
            )
            file_.write(
                "sample6:\n  assembly: sample6.fasta\n  cgmlst_scheme:\n  - null\n"
            )
        # TODO: This might change if we improve identification and then Shigella only needs to run one schema

        input_chewbbaca = chewbbaca_input_files.inputChewBBACA(
            sample_sheet="test_chewbbaca_per_genus/unsupported_sample_sheet.yaml",
            output_dir="test_chewbbaca_per_genus/output",
        )
        input_chewbbaca.make_file_with_samples_per_scheme()
        expected_output = {
            "escherichia": ["sample4.fasta", "sample5.fasta"],
            "listeria": ["sample3.fasta"],
            "listeria_optional": ["sample3.fasta"],
            "salmonella": ["sample1.fasta", "sample2.fasta"],
            "shigella": ["sample4.fasta", "sample5.fasta"],
        }
        actual_output = input_chewbbaca.cgmlst_scheme_dict
        print(actual_output)
        self.assertDictEqual(expected_output, actual_output, actual_output)


if __name__ == "__main__":
    unittest.main()
