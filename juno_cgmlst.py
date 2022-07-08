"""
Juno-cgMLST pipeline
Authors: Alejandra Hernandez-Segura
Organization: Rijksinstituut voor Volksgezondheid en Milieu (RIVM)
Department: Infektieziekteonderzoek, Diagnostiek en Laboratorium
            Surveillance (IDS), Bacteriologie (BPD)     
Date: 06-05-2022  

"""

# Dependencies
from base_juno_pipeline import *
from bin.version import __version__
import argparse
import pathlib
import subprocess
import yaml
import sys

# Own scripts
from bin import download_cgmlst_scheme


class JunoCgmlstRun(
    base_juno_pipeline.PipelineStartup, base_juno_pipeline.RunSnakemake
):
    """
    Class with the arguments and specifications that are only for the
    Juno-cgMLST pipeline but inherit from PipelineStartup and
    RunSnakemake
    """

    def __init__(
        self,
        input_dir,
        output_dir,
        genus=None,
        metadata=None,
        db_dir="/mnt/db/juno/cgmlst",
        cores=300,
        time_limit=60,
        local=False,
        queue="bio",
        unlock=False,
        rerunincomplete=False,
        dryrun=False,
        run_in_container=True,
        singularity_prefix=None,
        conda_prefix=None,
        **kwargs,
    ):
        """Initiating Juno-cgMLST pipeline"""

        # Get proper file paths
        output_dir = pathlib.Path(output_dir).resolve()
        workdir = pathlib.Path(__file__).parent.resolve()
        self.db_dir = pathlib.Path(db_dir).resolve()
        self.downloaded_schemes_dir = self.db_dir.joinpath("downloaded_schemes")
        self.prepared_schemes_dir = self.db_dir.joinpath("prepared_schemes")
        self.path_to_audit = output_dir.joinpath("audit_trail")
        self.cores = cores
        base_juno_pipeline.PipelineStartup.__init__(
            self,
            input_dir=pathlib.Path(input_dir).resolve(),
            input_type="fasta",
            min_num_lines=2,
        )  # Min for viable fasta
        base_juno_pipeline.RunSnakemake.__init__(
            self,
            pipeline_name="Juno_cgMLST",
            pipeline_version="v0.1",
            output_dir=output_dir,
            workdir=workdir,
            cores=self.cores,
            time_limit=time_limit,
            local=local,
            queue=queue,
            unlock=unlock,
            rerunincomplete=rerunincomplete,
            dryrun=dryrun,
            useconda=not run_in_container,
            conda_prefix=conda_prefix,
            usesingularity=run_in_container,
            singularityargs=f"--bind {self.input_dir}:{self.input_dir} --bind {output_dir}:{output_dir} --bind {db_dir}:{db_dir}",
            singularity_prefix=singularity_prefix,
            restarttimes=1,
            latency_wait=60,
            name_snakemake_report=str(
                self.path_to_audit.joinpath("juno_cgmlst_report.html")
            ),
            **kwargs,
        )

        # Pipeline attributes
        self.genus = genus
        self.metadata_file = metadata

        # Start pipeline
        self.run_juno_cgmlst_pipeline()

    def get_cgmlst_scheme_name(self):
        with open("files/dictionary_correct_cgmlst_scheme.yaml") as translation_yaml:
            self.cgmlst_scheme_translation_tbl = yaml.safe_load(translation_yaml)
        for sample in self.sample_dict:
            genus = self.sample_dict[sample]["genus"]
            try:
                self.sample_dict[sample][
                    "cgmlst_scheme"
                ] = self.cgmlst_scheme_translation_tbl[genus]
            except KeyError:
                self.sample_dict[sample]["cgmlst_scheme"] = [None]

    def update_sample_dict_with_metadata(self):
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
        self.get_cgmlst_scheme_name()

    def start_juno_cgmlst_pipeline(self):
        """
        Function to start the pipeline (some steps from PipelineStartup need
        to be modified for the Juno-cgmlst pipeline to accept fastq and fasta
        input
        """
        self.start_juno_pipeline()
        self.update_sample_dict_with_metadata()
        # Write sample_sheet
        with open(self.sample_sheet, "w") as file_:
            yaml.dump(self.sample_dict, file_, default_flow_style=False)

    def write_userparameters(self):

        config_params = {
            "input_dir": str(self.input_dir),
            "out": str(self.output_dir),
            "cgmlst_db": str(self.db_dir),
        }

        with open(self.user_parameters, "w") as file_:
            yaml.dump(config_params, file_, default_flow_style=False)

        return config_params

    def download_missing_schemes(self):
        all_needed_schemes = set()
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
        if len(all_needed_schemes) > 0:
            download_cgmlst_scheme.cgMLSTSchemes(
                threads=self.cores,
                genus_list=all_needed_schemes,
                download_loci=True,
                output_dir=self.downloaded_schemes_dir,
            )

    def run_juno_cgmlst_pipeline(self):
        self.start_juno_cgmlst_pipeline()
        self.user_params = self.write_userparameters()
        self.get_run_info()
        if not self.dryrun or self.unlock:
            self.path_to_audit.mkdir(parents=True, exist_ok=True)
            self.download_missing_schemes()

        self.successful_run = self.run_snakemake()
        assert self.successful_run, f"Please check the log files"
        if not self.dryrun or self.unlock:
            subprocess.run(
                f"find {self.output_dir} -type f -empty -exec rm {{}} \;", shell=True
            )
            subprocess.run(
                f"find {self.output_dir} -type d -empty -exec rm -rf {{}} \;",
                shell=True,
            )
            self.make_snakemake_report()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Juno-cgMLST pipeline. Automated pipeline for performing cgMLST or wgMLST."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=pathlib.Path,
        required=True,
        metavar="DIR",
        help="Relative or absolute path to the input directory. It must either be the output directory of the Juno-assembly pipeline or it must contain all the raw reads (fastq) and assemblies (fasta) files for all samples to be processed.",
    )
    parser.add_argument(
        "-m",
        "--metadata",
        type=pathlib.Path,
        default=None,
        required=False,
        metavar="FILE",
        help="Relative or absolute path to the metadata csv file. If "
        "provided, it must contain at least one column named 'sample' "
        "with the name of the sample (same than file name but removing "
        "the suffix _R1.fastq.gz) and a column called "
        "'genus'. The genus provided will be used to choose the "
        "cgMLST schema(s). If a metadata file is provided, it will "
        "overwrite the --genus argument for the samples present in "
        "the metadata file.",
    )
    parser.add_argument(
        "-g",
        "--genus",
        default=None,
        required=False,
        metavar="FILE",
        help="Genus name (any genus in the metadata file will overwrite"
        " this argument). It should be given as two words (e.g. "
        "--genus Salmonella)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=pathlib.Path,
        metavar="DIR",
        default="output",
        help="Relative or absolute path to the output directory. If non is given, an 'output' directory will be created in the current directory.",
    )
    parser.add_argument(
        "-d",
        "--db_dir",
        type=pathlib.Path,
        required=False,
        metavar="DIR",
        default="/mnt/db/juno/cgmlst",
        help="Relative or absolute path to the directory that contains the databases for all the tools used in this pipeline or where they should be downloaded. Default is: /mnt/db/juno/cgmlst",
    )
    parser.add_argument(
        "-c",
        "--cores",
        type=int,
        metavar="INT",
        default=300,
        help="Number of cores to use. Default is 300",
    )
    parser.add_argument(
        "-q",
        "--queue",
        type=str,
        metavar="STR",
        default="bio",
        help="Name of the queue that the job will be submitted to if working on a cluster.",
    )
    parser.add_argument(
        "-w",
        "--time-limit",
        type=int,
        metavar="INT",
        default=60,
        help="Time limit per job in minutes (passed as -W argument to bsub). Jobs will be killed if not finished in this time.",
    )
    parser.add_argument(
        "-l",
        "--local",
        action="store_true",
        help="Running pipeline locally (instead of in a computer cluster). Default is running it in a cluster.",
    )
    # Snakemake arguments
    parser.add_argument(
        "-u",
        "--unlock",
        action="store_true",
        help="Unlock output directory (passed to snakemake).",
    )
    parser.add_argument(
        "-n",
        "--dryrun",
        action="store_true",
        help="Dry run printing steps to be taken in the pipeline without actually running it (passed to snakemake).",
    )
    parser.add_argument(
        "--rerunincomplete",
        action="store_true",
        help="Re-run jobs if they are marked as incomplete (passed to snakemake).",
    )
    parser.add_argument(
        "--snakemake-args",
        nargs="*",
        default={},
        action=helper_functions.SnakemakeKwargsAction,
        help="Extra arguments to be passed to snakemake API (https://snakemake.readthedocs.io/en/stable/api_reference/snakemake.html).",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=__version__,
        help="Show Juno_cgmlst version number and exit",
    )
    args = parser.parse_args()
    JunoCgmlstRun(
        input_dir=args.input,
        output_dir=args.output,
        genus=args.genus,
        metadata=args.metadata,
        db_dir=args.db_dir,
        cores=args.cores,
        time_limit=args.time_limit,
        local=args.local,
        queue=args.queue,
        unlock=args.unlock,
        rerunincomplete=args.rerunincomplete,
        dryrun=args.dryrun,
        run_in_container=False,
        singularity_prefix=None,
        conda_prefix=None,
        **args.snakemake_args,
    )
