"""
Juno-cgMLST pipeline
Authors: Alejandra Hernandez-Segura
Organization: Rijksinstituut voor Volksgezondheid en Milieu (RIVM)
Department: Infektieziekteonderzoek, Diagnostiek en Laboratorium
            Surveillance (IDS), Bacteriologie (BPD)
Date: 06-05-2022

"""

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml

# Dependencies
from juno_library import Pipeline

# Own scripts
from bin import download_cgmlst_scheme
from version import __package_name__, __version__


def main(args: list[str] | None = None) -> None:

    if args is not None:
        juno_cgmlst = JunoCgmlst(args)
    else:
        juno_cgmlst = JunoCgmlst()
    juno_cgmlst.run()


@dataclass
class JunoCgmlst(Pipeline):
    """
    Class with the arguments and specifications that are only for the
    Juno-cgMLST pipeline but inherit from PipelineStartup and
    RunSnakemake
    """

    pipeline_name: str = __package_name__
    pipeline_version: str = __version__
    input_type: str = "fasta"
    min_num_lines: int = 2

    def _add_args_to_parser(self) -> None:
        super()._add_args_to_parser()

        self.parser.description = "Juno-typing pipeline. Automated pipeline for bacterial subtyping (7-locus MLST and serotyping)."
        self.add_argument(
            "-g",
            "--genus",
            type=lambda s: s.strip().lower(),
            default=None,
            required=True,
            metavar="GENUS",
            help="Genus name (any species in the metadata file will overwrite this argument).",
        )
        self.add_argument(
            "-d",
            "--db_dir",
            type=Path,
            required=False,
            metavar="DIR",
            default="/mnt/db/juno/cgmlst",
            help="Relative or absolute path to the directory that contains the databases for all the tools used in this pipeline or where they should be downloaded. Default is: /mnt/db/juno/cgmlst",
        )
        self.add_argument(
            "-m",
            "--metadata",
            type=Path,
            default=None,
            required=False,
            metavar="FILE",
            help="Relative or absolute path to the metadata csv file. If "
            "provided, it must contain at least one column named 'sample' "
            "with the name of the sample (same than file name but removing "
            "the suffix _R1.fastq.gz), a column called "
            "'genus' and a column called 'species'. The genus and species "
            "provided will be used to choose the serotyper and the MLST schema(s)."
            "If a metadata file is provided, it will overwrite the --species "
            "argument for the samples present in the metadata file.",
        )

    def _parse_args(self) -> argparse.Namespace:
        # Remove this if containers can be used with juno-typing
        if "--no-containers" not in self.argv:
            self.argv.append("--no-containers")

        args = super()._parse_args()
        self.genus = args.genus
        self.db_dir: Path = args.db_dir
        self.downloaded_schemes_dir = self.db_dir.joinpath("downloaded_schemes")
        self.prepared_schemes_dir = self.db_dir.joinpath("prepared_schemes")
        self.metadata_file: Path = args.metadata
        return args

    def set_scheme_in_sample_dict(self) -> None:
        with open("files/dictionary_correct_cgmlst_scheme.yaml") as translation_yaml:
            self.cgmlst_scheme_translation_tbl = yaml.safe_load(translation_yaml)
        for sample in self.sample_dict:
            genus = self.sample_dict[sample]["genus"]
            try:
                self.sample_dict[sample]["cgmlst_scheme"] = (
                    self.cgmlst_scheme_translation_tbl[genus]
                )
            except KeyError:
                self.sample_dict[sample]["cgmlst_scheme"] = ""

    def update_sample_dict_with_metadata(self) -> None:
        self.get_metadata_from_csv_file(
            filepath=self.metadata_file, expected_colnames=["sample", "genus"]
        )
        # Add metadata
        for sample in self.sample_dict:
            if self.genus is not None:
                self.sample_dict[sample]["genus"] = self.genus
            else:
                try:
                    self.sample_dict[sample].update(self.juno_metadata[sample])
                except (KeyError, TypeError):
                    raise ValueError(
                        f"One of your samples is not in the metadata file "
                        f"({self.metadata_file}). Please ensure that all "
                        "samples are present in the metadata file or provide "
                        "a --genus argument."
                    )
                self.sample_dict[sample]["genus"] = (
                    self.sample_dict[sample]["genus"].strip().lower()
                )
        self.set_scheme_in_sample_dict()

    def setup(self) -> None:
        super().setup()
        self.update_sample_dict_with_metadata()
        self.user_parameters = {
            "input_dir": str(self.input_dir),
            "out": str(self.output_dir),
            "cgmlst_db": str(self.db_dir),
        }

        with open(
            Path(__file__).parent.joinpath("config/pipeline_parameters.yaml")
        ) as f:
            parameters_dict = yaml.safe_load(f)
        self.snakemake_config.update(parameters_dict)

    def download_missing_schemes(self) -> None:
        all_needed_schemes: set[str] = set()
        for sample in self.sample_dict:
            try:
                schemes = self.sample_dict[sample]["cgmlst_scheme"]
            except:
                raise ValueError(
                    f"There is no cgmlst_scheme assigned to sample {sample}"
                    " Did you try to look for the scheme before you assigned "
                    "metadata to the samples?"
                )
            for scheme in schemes:
                if scheme is not None:
                    if not self.prepared_schemes_dir.joinpath(scheme).is_dir():
                        end_file_download = self.downloaded_schemes_dir.joinpath(
                            scheme, "downloaded_scheme.yaml"
                        )
                        if not end_file_download.is_file():
                            all_needed_schemes.add(scheme)
        if all_needed_schemes:
            download_cgmlst_scheme.cgMLSTSchemes(
                threads=self.snakemake_args["cores"],
                genus_list=all_needed_schemes,
                download_loci=True,
                output_dir=str(self.downloaded_schemes_dir),
            )

    def run_juno_cgmlst_pipeline(self) -> None:
        self.setup()
        if not self.dryrun or self.unlock:
            self.path_to_audit.mkdir(parents=True, exist_ok=True)
            self.download_missing_schemes()
        super().run()
        if not self.dryrun or self.unlock:
            subprocess.run(
                f"find {self.output_dir} -type f -empty -exec rm {{}} \;", shell=True
            )
            subprocess.run(
                f"find {self.output_dir} -type d -empty -exec rm -rf {{}} \;",
                shell=True,
            )


if __name__ == "__main__":
    main()
