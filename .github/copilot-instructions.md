# Juno-cgMLST Pipeline - AI Coding Instructions

## Project Overview
Juno-cgMLST is a Snakemake-based bacterial genomics pipeline that performs core genome MLST (cgMLST) analysis using ChewBBACA. It processes bacterial assembly files (.fasta) and generates allele profiles with SHA1 hashes for reproducible sharing.

## Key Architecture Components

### Pipeline Entry Point
- `juno_cgmlst.py` - Main pipeline orchestrator inheriting from `juno_library.Pipeline`
- Uses dataclass pattern with `@dataclass` decorator for configuration
- Key workflow: setup → download schemes → run Snakemake → cleanup

### Genus-to-Scheme Mapping
- `files/dictionary_correct_cgmlst_scheme.yaml` - **CRITICAL**: Maps bacterial genus to cgMLST schemes
- Some genera use multiple schemes (e.g., STEC uses escherichia, shigella, stec)
- This mapping drives the entire analysis workflow

### Snakemake Workflow (`Snakefile`)
- Rule `enlist_samples_for_cgmlst_scheme` → groups samples by scheme
- Rule `cgmlst_per_scheme` → runs ChewBBACA per scheme via bash script
- Produces both allele numbers (`results_alleles.tsv`) and SHA1 hashes (`results_alleles_hashed.tsv`)

## Critical Patterns & Workflows

### Sample Processing Flow
1. Parse metadata CSV → assign genus to samples
2. Map genus to cgMLST schemes using dictionary
3. Group samples by scheme (one sample can use multiple schemes)
4. Download missing schemes if needed
5. Run ChewBBACA per scheme group
6. Generate both numeric and hashed results

### ChewBBACA Integration (`bin/chewbbaca_per_genus.sh`)
- **Database Locking**: ChewBBACA locks the entire database during analysis
- Two-stage process: PrepExternalSchema → AlleleCall
- Uses genus-specific Prodigal training files from `files/prodigal_training_files/`
- Always run with `--no-inferred --hash-profiles sha1`

### Scheme Management
- **Downloaded**: Raw schemes in `{db_dir}/downloaded_schemes/`
- **Prepared**: ChewBBACA-ready schemes in `{db_dir}/prepared_schemes/`
- Preparation only happens once per scheme via `PrepExternalSchema`

## Development Conventions

### File Organization
- `bin/` - Helper scripts (Python + bash)
- `config/` - Pipeline parameters and resource allocation
- `envs/` - Conda environment definitions
- `files/` - Static data (scheme mappings, training files)

### Error Handling Patterns
- Use `set -euo pipefail` in bash scripts
- Validate metadata presence before processing
- Check for prepared schemes before ChewBBACA runs

### Testing Strategy
- Unit tests in `tests/` for core functionality
- Example input/output in `tests/example_*` directories
- Test both scheme downloads and ChewBBACA processing

## Integration Points

### External Dependencies
- **ChewBBACA**: Core tool, requires specific conda environment
- **Juno Library**: Shared pipeline framework (`juno_library.Pipeline`)
- **Multiple databases**: PubMLST, Enterobase, SeqSphere+, BIGSDB Pasteur

### Cluster Integration
- Default: RIVM cluster with LSF scheduler
- Resource allocation via `config/pipeline_parameters.yaml`
- Time limits crucial for large datasets (>30 samples need `--time-limit >60`)

## Common Debugging Scenarios

### Database Conflicts
If ChewBBACA fails with database lock errors, check for concurrent runs using same scheme in `prepared_schemes/` directory.

### Missing Schemes
Pipeline auto-downloads missing schemes, but verify `files/dictionary_correct_cgmlst_scheme.yaml` has correct genus mapping.

### Memory Issues
ChewBBACA is memory-intensive. Default 24GB per job; increase for large schemes or many samples.

## Key Files for Understanding
- `juno_cgmlst.py` - Main pipeline logic and setup
- `Snakefile` - Workflow definition and rule dependencies  
- `bin/chewbbaca_per_genus.sh` - ChewBBACA execution wrapper
- `files/dictionary_correct_cgmlst_scheme.yaml` - Genus-to-scheme mapping
- `bin/download_cgmlst_scheme.py` - Multi-source scheme downloader

## Development Tips
- Always test with small datasets first (ChewBBACA is slow)
- Verify scheme mapping before adding new genera
- Check Prodigal training file availability for new genera
- Consider database locking when debugging concurrent runs