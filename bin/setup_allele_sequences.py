"""
Given the output of chewBBACA GetAlleles, this module will create a csv file with two columns.
The first column will be the 128-bit hash of the allele sequence,
and the second column will be the allele sequence itself.
"""

import argparse
import csv
import hashlib
import os


def list_fasta_files(input_dir: str) -> list[str]:
    """List all fasta files in the given directory."""

    fasta_files: list[str] = []
    for file in os.listdir(input_dir):
        if file.endswith(".fasta") or file.endswith(".fa"):
            fasta_files.append(os.path.join(input_dir, file))
    return fasta_files


def import_fasta(fasta_file: str) -> dict[str, str]:
    """Open a fasta file and return a dictionary with the header as key and sequence as value."""
    sequences: dict[str, str] = {}
    with open(fasta_file, "r", encoding="utf-8") as f:
        header = ""
        seq_lines: list[str] = []
        for line in f:
            line = line.strip()
            if line.startswith(">"):
                if header:
                    sequences[header] = "".join(seq_lines)
                seq_lines = []
            else:
                seq_lines.append(line)
        if header:
            sequences[header] = "".join(seq_lines)
    return sequences


def replace_header_with_hash(sequences: dict[str, str]) -> dict[str, str]:
    """Replace the header of each sequence with its 128-bit hash."""

    hashed_sequences: dict[str, str] = {}
    for _, sequence in sequences.items():
        hash_object = hashlib.md5(sequence.encode())
        hash_hex = hash_object.hexdigest()
        hashed_sequences[hash_hex] = sequence
    return hashed_sequences


def export_to_csv(sequences: dict[str, str], output_file: str) -> None:
    """Export the sequences to a csv file with two columns: hash and sequence."""
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Hash", "Sequence"])
        for hash_key, sequence in sequences.items():
            writer.writerow([hash_key, sequence])


def parse_args() -> tuple[str, str]:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process allele sequences from chewBBACA GetAlleles output."
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Input directory of fasta files from chewBBACA GetAlleles output.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output CSV file to store hash and sequence.",
    )

    args = parser.parse_args()
    return args.input, args.output


def main() -> None:
    """Main function to process allele sequences."""
    input_dir, output_file = parse_args()
    fasta_files = list_fasta_files(input_dir)
    all_sequences: dict[str, str] = {}
    for fasta_file in fasta_files:
        sequences = import_fasta(fasta_file)
        all_sequences.update(sequences)
    hashed_sequences = replace_header_with_hash(all_sequences)
    export_to_csv(hashed_sequences, output_file)


if __name__ == "__main__":
    main()
