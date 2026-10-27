"""
Juno-cgMLST
Author(s): Alejandra Hernandez-Segura, Kaitlin Weber, Edwin van der Kind and Maaike van den Beld
Organization: Rijksinstituut voor Volksgezondheid en Milieu (RIVM)
Department: Infektieziekteonderzoek, Diagnostiek en Laboratorium Surveillance (IDS), Bacteriologie (BPD)
Date: 06-05-2022
"""
#################################################################################
##### Import config file, sample_sheet and set output folder names          #####
#################################################################################

from os.path import getsize, exists, abspath
from yaml import safe_load

#################################################################################
#####     Load samplesheet, load genus dict and define output directory     #####
#################################################################################

# Loading sample sheet as dictionary
sample_sheet = config["sample_sheet"]
SAMPLES = {}
with open(sample_sheet) as sample_sheet_file:
    SAMPLES = safe_load(sample_sheet_file)
SCHEMES = set()
for sample in SAMPLES:
    for scheme_ in SAMPLES[sample]["cgmlst_scheme"]:
        if scheme_:
            SCHEMES.add(scheme_)

# OUT defines output directory for most rules.
OUT = config["out"]
CGMLST_DB = config["cgmlst_db"]


#################################################################################
#####                       Specify final output                            #####
#################################################################################


localrules:
    all,
    copy_mlst_config,


rule all:
    input:
        expand(OUT + "/cgmlst/{scheme}/results_alleles.tsv", scheme=SCHEMES),
        expand(OUT + "/cgmlst/{scheme}/results_alleles_hashed.tsv", scheme=SCHEMES),
        OUT + "/audit_trail/mlst_config.yaml",


#################################################################################
#####                    Copy config to audit trail                         #####
#################################################################################

rule copy_mlst_config:
    input:
        "config/mlst_config.yaml"
    output:
        OUT + "/audit_trail/mlst_config.yaml"
    message:
        "Copying MLST configuration to audit trail"
    shell:
        "cp {input} {output}"


# @################################################################################
# @####                              Processes                                #####
# @################################################################################


rule enlist_samples_for_cgmlst_scheme:
    input:
        sample_sheet,
    output:
        temp(expand(OUT + "/cgmlst/{scheme}_samples.txt", scheme=SCHEMES)),
    message:
        "Finding which cgMLST scheme needs to be run for each sample."
    log:
        OUT + "/log/cgmlst/list_samples_per_cgmlst_scheme.log",
    threads: int(config["threads"]["other"])
    resources:
        mem_gb=int(config["mem_gb"]["other"]),
    params:
        output_dir=OUT + "/cgmlst",
    shell:
        """
python bin/chewbbaca_input_files.py --sample-sheet {input} \
    --output-dir {params.output_dir} &> {log}
        """


# ----------------------- Choose cgMLST scheme per genus ----------------------#


rule cgmlst_per_scheme:
    input:
        input_files=OUT + "/cgmlst/{scheme}_samples.txt",
    output:
        chewbbaca_result=OUT + "/cgmlst/{scheme}/results_alleles.tsv",
        chewbbaca_hashed=OUT + "/cgmlst/{scheme}/results_alleles_hashed.tsv",
        chewbbaca_sequences=directory(OUT + "/cgmlst/{scheme}/GetAlleles_output/"),
    message:
        "Running cgMLST for scheme {wildcards.scheme}"
    conda:
        "envs/chewbbaca.yaml"
    log:
        OUT + "/log/cgmlst/chewbbaca_{scheme}.log",
    threads: int(config["threads"]["chewbbaca"])
    resources:
        mem_gb=int(config["mem_gb"]["chewbbaca"]),
    params:
        output_dir=abspath(OUT + "/cgmlst/{scheme}"),
        db_dir=CGMLST_DB,
    shell:
        """
bash bin/chewbbaca_per_genus.sh {input.input_files} \
    {threads} \
    {params.output_dir} \
    {params.db_dir} \
    {wildcards.scheme} &> {log}
        """


# ----------------------- Hash cgMLST results alleles ------------------------#

# rule hash_cgmlst:
#     input:
#         OUT + '/cgmlst/{scheme}/results_alleles.tsv'
#     output:
#         OUT + '/cgmlst/{scheme}/hashed_results_alleles.csv'
#     message: "Getting hashes for the cgMLST results for scheme {wildcards.scheme}"
#     log:
#         OUT + '/log/cgmlst/hashed_chewbbaca_{scheme}.log'
#     threads: config['threads']['other']
#     resources: mem_gb=config['mem_gb']['other']
#     params:
#         db_dir = CGMLST_DB + '/prepared_schemes/',
#         scheme = '{scheme}'
#     shell:
#         """
# python bin/get_allele_hashes.py --scheme-name {params.scheme} \
#                                 --output {output} \
#                                 --db-dir {params.db_dir} \
#                                 --threads {threads} \
#                                 {input} &> {log}
#         """


# @################################################################################
# @####              Finalize pipeline (error/success)                        #####
# @################################################################################


onerror:
    shell(
        """
find -maxdepth 1 -type d -empty -exec rm -rf {{}} \;
echo -e "Something went wrong with Juno-cgMLST pipeline. Please check the logging files in {OUT}/log/"
    """
    )
