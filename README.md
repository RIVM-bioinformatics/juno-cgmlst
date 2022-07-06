<div align="center">
    <h1>Juno_cgMLST</h1>
    <br />
    <h2>Pipeline to perform cgMLST (or wgMLST) analysis.</h2>
    <br />
    <img src="https://via.placeholder.com/150" alt="pipeline logo">
</div>

## Pipeline information

* **Author(s):**            Alejandra Hernández Segura
* **Organization:**         Rijksinstituut voor Volksgezondheid en Milieu (RIVM)
* **Department:**           Infektieziekteonderzoek, Diagnostiek en Laboratorium Surveillance (IDS), Bacteriologie (BPD)
* **Start date:**           06 - 05 - 2022

## About this project

The goal of this pipeline is to perform cgMLST on bacterial genomes. As input, it requires an assembly for each sample you want to analyze in the form of a single ‘.fasta’ file.

Importantly, the Juno-cgMLST pipeline also works directly on output generated from the [Juno-assembly pipeline](https://github.com/RIVM-bioinformatics/Juno_pipeline).

The Juno-cgMLST uses [ChewBBACA](https://github.com/B-UMMI/chewBBACA/) to find the cgMLST profile of the given genomes. Besides, the result table with the allele numbers is translated to a table with (sha1) hashes so that they can be shared and compared even if each result used a different database. **Note:** We highly encourage to use the hashes for the analysis instead of the allele numbers. This will make your data more reproducible in case there was an update in the database that assigns allele numbers or to share it with other colleagues.

## Prerequisities

* **Linux + conda** A Linux-like environment with at least 'miniconda' installed. 
* **Python3.7.6** .


## Installation

1. Clone the repository:

```
git clone https://github.com/RIVM-bioinformatics/Juno_cgmlst.git
```
Alternatively, you can download it manually as a zip file (you will need to unzip it then).

2. Enter the directory with the pipeline and install the master environment:

```
cd Juno_cgmlst
conda env update -f envs/master_env.yaml
```

## Parameters & Usage

### Command for help

* ```-h, --help``` Shows the help of the pipeline

### Required parameters

* ```-i, --input``` Directory with the input (fasta) files. The fasta files should be all in this directory (no subdirectories) and have the extension '.fasta'. 

### Optional parameters

```
  -h, --help            show this help message and exit
  -i DIR, --input DIR   Relative or absolute path to the input directory. It
                        must either be the output directory of the Juno-
                        assembly pipeline or it must contain all the raw reads
                        (fastq) and assemblies (fasta) files for all samples
                        to be processed.
  -m FILE, --metadata FILE
                        Relative or absolute path to the metadata csv file. If
                        provided, it must contain at least one column named
                        'sample' with the name of the sample (same than file
                        name but removing the suffix _R1.fastq.gz) and a
                        column called 'genus'. The genus provided will be used
                        to choose the cgMLST schema(s). If a metadata file is
                        provided, it will overwrite the --genus argument for
                        the samples present in the metadata file.
  -g FILE, --genus FILE
                        Genus name (any genus in the metadata file will
                        overwrite this argument). It should be given as two
                        words (e.g. --genus Salmonella)
  -o DIR, --output DIR  Relative or absolute path to the output directory. If
                        non is given, an 'output' directory will be created in
                        the current directory.
  -d DIR, --db_dir DIR  Relative or absolute path to the directory that
                        contains the databases for all the tools used in this
                        pipeline or where they should be downloaded. Default
                        is: /mnt/db/juno/cgmlst_db
  -c INT, --cores INT   Number of cores to use. Default is 300
  -q STR, --queue STR   Name of the queue that the job will be submitted to if
                        working on a cluster.
  -w INT, --time-limit INT
                        Time limit per job in minutes (passed as -W argument
                        to bsub). Jobs will be killed if not finished in this
                        time.
  -l, --local           Running pipeline locally (instead of in a computer
                        cluster). Default is running it in a cluster.
  -u, --unlock          Unlock output directory (passed to snakemake).
  -n, --dryrun          Dry run printing steps to be taken in the pipeline
                        without actually running it (passed to snakemake).
  --rerunincomplete     Re-run jobs if they are marked as incomplete (passed
                        to snakemake).
  --snakemake-args [SNAKEMAKE_ARGS [SNAKEMAKE_ARGS ...]]
                        Extra arguments to be passed to snakemake API (https:/
                        /snakemake.readthedocs.io/en/stable/api_reference/snak
                        emake.html).
  --version, -v         Show Jonu_cgmlst version number and exit

```

Example metadata file:

| __sample__ | __genus__ |
| :---: | :--- |
| sample1 | salmonella |

*Note:* The fastq files corresponding to this sample would probably be something like sample1_S1_R1_0001.fastq.gz and sample2_S1_R1_0001.fastq.gz and the fasta file sample1.fasta. Also note that the column titles of the metadata.csv file are all in lower case.

### The base command to run this program. 

```
python juno_cgmlst.py -i [dir/to/input_directory] 
```

### An example on how to run the pipeline.

```
python juno_cgmlst.py -i my_input_dir -o my_results_dir --db_dir my_db_dir --metadata path/to/my/metadata.csv
```

**Note for large datasets:** If your dataset is large (more than 30 samples), t is necessary to give the pipeline extra time to process samples. This means that it needs to run with the `-w` or `--time-limit` argument. The default is 60 (minutes) but for large datasets (more than 30 samples) it should be increased accordingly Example:

```
python juno_cgmlst.py -i my_large_input_dir -o my_results_dir --db_dir my_db_dir --metadata path/to/my/metadata.csv --time-limit 120
```

## Explanation of the output

* **log:** Log files with output and error files from each Snakemake rule/step that is performed. 
* **audit_trail:** Information about the versions of software and databases used.
* **output per sample:** The pipeline will create one subfolder per each step performed. These subfolders will in turn contain another subfolder per sample. To understand the output, please refer to the manual of ChewBBACA.
        
## Issues  

* ChewBBACA can be very slow so for large datasets it is necessary to give the pipeline extra time to process samples. This means that it needs to run with the `-w` or `--time-limit` argument. The default is 60 (minutes) but for large datasets (more than 30 samples) it should be increased accordingly.
* All default values have been chosen to work with the RIVM Linux environment, therefore, there might not be applicable to other environments (although they should work if the appropriate arguments/parameters are given).
* ChewBBACA has some inherent 'issues' that are known:
    - The analysis of separate samples is not completely parallelized. ChewBBACA tries to optimize the analysis but many steps have to be shared between samples. **ChewBBACA blocks the directory with the database** so that **two different analyses cannot be done using the same database at the same time**. This has a reason and that is that if a new allele is found in your dataset, ChewBBACA ensures that a new allele number gets assigned to it and that this one is not concurrently assigned by another running process in the same database. However, this feature can be really problematic for databases where multiple people might be using the pipeline at the same time (as may be the case at the RIVM). You cannot put samples running in parallel (which might be only moderately more efficient anyway because of the shared steps which are long anyway) and more importantly, two people cannot be running an analysis at the same time. This includes automated runs in which samples from different genera, such as _Shigella_  and _Escherichia_ will be processed at the same time and both will be running the same cgMLST scheme but would interfere with each other causing the crash of one of them.   
    - Every time a new allele is found for a schema, it can cause some results to lose reproducibility. In these
     cases, the allele distance might be underestimated so this means that the ability to detect a sample as part of an outbreak would not decrease. You would, however, include more false positives. It is something that can be tolerated for our purposes but can cause confusion among analysts. It, in theory, should be improved once your database is more stable and no more novel alleles are found. The explanation of why that happens can be found [here](https://github.com/B-UMMI/chewBBACA/issues/115).  
* Any issue can be reported in the [Issues section](https://github.com/RIVM-bioinformatics/Juno-typing/issues) of this repository.

## Future ideas for this pipeline

* Include the hashing within the ChewBBACA algorithm.  
* Build and pair a database for the alleles and loci to store the information about the sequences.  
* Optimize the algorithm of ChewBBACA by not locking the whole database during the whole duration of the analysis.  

## License
This pipeline is licensed with an AGPL3 license. Detailed information can be found inside the 'LICENSE' file in this repository.

## Contact
* **Contact person:**       Roxanne Wolthuis
* **Email**                 roxanne.wolthuis@rivm.nl
