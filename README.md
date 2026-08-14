

## Usage



### Table Extraction

Run `uv run extract_tables.py` to extract tables from a running Zotero instance.

This produces the directories `extracted_tables` and `paper_data`. `extract_tables` contains screenshots and annotation text for the marked tables. `paper_data` contains paper metadata (including the tables which are included in it).


## Score Extraction

- Run `uv run scores_from_tables.py` (or `sbatch scores_from_tables.slurm`) to extract the scores from the screenshots (using the additional information and the prompt template).


### Installing the correct dependencies


- Create environment using `uv`: `uv venv`
- Manually install the correct torch version.
- Install the other dependencies: `uv pip install -c constraints.txt -r requirements.txt` 
- Lock dependencies: `uv lock`




### Evaluation Example

```bash
uv run --locked  extract.py
```
