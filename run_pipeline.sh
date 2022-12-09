#!/bin/bash

# Wrapper for juno AMR pipeline

set -euo pipefail

#----------------------------------------------#
# User parameters
if [ ! -z "${1}" ] || [ ! -z "${2}" ] || [ ! -z "${irods_input_projectID}" ]
then
   input_dir="${1}"
   output_dir="${2}"
   PROJECT_NAME="${irods_input_projectID}"
else
    echo "One of the parameters is missing, make sure there is an input directory, output directory and project name(param 1, 2 or irods_input_projectID)."
    exit 1
fi

# if [ ! -d "${input_dir}" ] || [ ! -d "${output_dir}" ] || [ ! -d "${input_dir}/clean_fastq" ]
# then
#   echo "The input directory $input_dir, output directory $output_dir or fastq dir ${input_dir}/clean_fastq does not exist"
#   exit 1
# else
#   input_fastq="${input_dir}/clean_fastq"
# fi



#----------------------------------------------#
# Create/update necessary environments
PATH_MAMBA_YAML="envs/mamba.yaml"
PATH_MASTER_YAML="envs/juno_cgmlst.yaml"
MAMBA_NAME=$(head -n 1 ${PATH_MAMBA_YAML} | cut -f2 -d ' ')
MASTER_NAME=$(head -n 1 ${PATH_MASTER_YAML} | cut -f2 -d ' ')

echo -e "\nUpdating necessary environments to run the pipeline..."

# Removing strict mode because it sometimes breaks the code for 
# activating an environment and for testing whether some variables
# are set or not
set +euo pipefail 

conda env update -f "${PATH_MAMBA_YAML}"
source activate "${MAMBA_NAME}"

mamba env update -f "${PATH_MASTER_YAML}"

source activate "${MASTER_NAME}"

set -euo pipefail


if [ ! -z ${irods_runsheet_sys__runsheet__lsf_queue} ]; then
    QUEUE="${irods_runsheet_sys__runsheet__lsf_queue}"
else
    QUEUE="bio"
fi

case $PROJECT_NAME in
  svstec)
    GENUS_ALL="escherichia shigella stec"
    GENUS="stec"
    ;;
  svshig)
    GENUS_ALL="escherichia shigella"
    GENUS="shigella"
    ;;
  salm)
    GENUS_ALL="salmonella"
    GENUS="salmonella"
    ;;
  campy)
    GENUS_ALL="campylobacter"
    GENUS="campylobacter"
    ;;
  svlismon)
    GENUS_ALL="listeria listeria_optional"
    GENUS="listeria"
    ;;
  yers)
    GENUS_ALL="yersinia"
    GENUS="yersinia"
    ;;
  *)
    GENUS_ALL="other"
    ;;
esac

#----------------------------------------------#
# Copying database directory if it exists
DB_DIR="schemes"
for G in $GENUS_ALL
do
  echo -e "\nCopying the cgMLST schema from /mnt/db/juno/cgmlst/prepared_schemes/$G..."
  mkdir -p "$DB_DIR/prepared_schemes"
  cp -r --no-preserve=mode,ownership "/mnt/db/juno/cgmlst/prepared_schemes/$G" "$DB_DIR/prepared_schemes/$G"
  cp --no-preserve=mode,ownership /mnt/db/juno/cgmlst/prepared_schemes/${G}_{sum,inv}*.txt "$DB_DIR/prepared_schemes/"
done

#----------------------------------------------#
# Run the pipeline
echo -e "\nRun pipeline..."

python juno_cgmlst.py \
    --queue "$QUEUE" \
    -i "$input_dir" \
    -o "$output_dir" \
    -g "$GENUS" \
    -d "$DB_DIR"

result=$?

#----------------------------------------------#
# Propagate metadata
set +euo pipefail

SEQ_KEYS=
SEQ_ENV=`env | grep irods_input_sequencing`
for SEQ_AVU in ${SEQ_ENV}
do
    SEQ_KEYS="${SEQ_KEYS} ${SEQ_AVU%%=*}"
done

for key in $SEQ_KEYS irods_input_illumina__Flowcell irods_input_illumina__Instrument \
    irods_input_illumina__Date irods_input_illumina__Run_number irods_input_illumina__Run_Id
do
    if [ ! -z ${!key} ] ; then
        attrname=${key:12}
        attrname=${attrname/__/::}
        echo "${attrname}: '${!key}'" >> ${OUTPUTDIR}/metadata.yml
    fi
done

set -euo pipefail

#----------------------------------------------#
# END
exit ${result}
