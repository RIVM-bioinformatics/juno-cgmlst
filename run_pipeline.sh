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


#----------------------------------------------#
# Create/update necessary environments
MAIN_ENV_YAML="envs/juno_cgmlst.yaml"
MAIN_ENV=$(head -n 1 ${MAIN_ENV_YAML} | cut -f2 -d ' ')

echo -e "\nUpdating necessary environments to run the pipeline..."

# Removing strict mode because it sometimes breaks the code for 
# activating an environment and for testing whether some variables
# are set or not
set +euo pipefail

mamba env update -f "${MAIN_ENV_YAML}"

source activate "${MAIN_ENV}"

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

DB_DIR="/mnt/db/juno/cgmlst/"

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
