set -euo pipefail
set -x

# Input user
input_files=$(realpath "$1")
threads="$2"
output_dir="$3"
db_dir=$(realpath "$4")
genus="$5"

# Make new variables
downloaded_scheme="${db_dir}/downloaded_schemes/${genus}"
prepared_scheme="${db_dir}/prepared_schemes/${genus}"
script_path="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
prodigal_training_file=$(realpath "$script_path/../files/prodigal_training_files/${genus}.trn")

echo "Deleting any previous results from old ChewBBACA runs if existing in ${output_dir}...\n"
rm -rf "results_*"  

if [ ! -f "$db_dir/prepared_schemes/$genus/$genus.trn" ]; then
    echo "Preparing scheme for running it with ChewBBACA..."
    chewBBACA.py PrepExternalSchema -i "$downloaded_scheme" \
        --output-directory "$prepared_scheme" \
        --cpu $threads \
        --ptf "$prodigal_training_file"
    echo "Prepared scheme can be found at ${prepared_scheme}.\n"
fi

echo "Making output directory ${output_dir}...\n"
mkdir -p ${output_dir}
cd "${output_dir}"

echo "Running ChewBBACA for ${genus} scheme...\n"
chewBBACA.py AlleleCall --cpu ${threads} \
                -i "${input_files}" \
                -o "." \
                -g "${prepared_scheme}" \
                --no-inferred \
                --hash-profiles sha1
                # --ptf "$prodigal_training_file" \
                # --fr


# Check if AlleleCall produced the expected results
if [ ! -f "results_alleles.tsv" ] || [ ! -f "results_alleles_hashed.tsv" ]; then
    echo "Error: AlleleCall did not produce expected results files"
    exit 1
fi


mkdir -p "GetAlleles_output"
chewBBACA.py GetAlleles --input "." \
                --output-directory "GetAlleles_output" \
                -g "${prepared_scheme}" \
                --cpu ${threads}


# The newly identified alleles have the 'INF-' prefix
# That can cause issues when calculating the distance matrix
# because they will be seen as diferent from the alleles
# that do not have the prefix. Therefore it is better to remove them
# sed -i -r "s/INF-([0-9]+)/\1/g" "results_alleles.tsv"
