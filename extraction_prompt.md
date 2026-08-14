# EXTRACTION TASK

Convert table cells into a JSON-formatted list of entries. Each metric cell usually corresponds to one entry, populated with row-level metadata (shared across the row) and cell-level metadata (specific to that cell).

Do not create a separate entry for the number of parameters (treat it as metadata for the other entries).

## WORKFLOW

1. Extract all interpretable metric cells; create entries with available data and `null` for missing/unclear fields
2. Identify and list all issues affecting data quality
3. For each issue, note affected rows and fields

## TABLE STRUCTURE & FIELD LOCATIONS

A table contains column headers, row headers (leftmost), data cells, and optional additional info (captions, notes, metadata).

Fields can reside in three locations:

1. Additional info: Explicitly provided text, captions, or metadata
2. Row headers: Applies to all entries in that row
3. Column headers: Applies to a single column or column group


## ENTRY STRUCTURE

Each entry has the following fields:
{field_descriptions}

Some values are shared across all cells in a row, some are cell-specific.

## FIELD ASSIGNMENT RULES

| Scenario | Action |
|----------|--------|
| metric_name unavailable |	Assign null (always include field) |
| Column missing & not in additional info | Omit field entirely (e.g., trained_parameters if no #Params column exists) |
| Column exists but cell empty | Assign `null` |
| Cell unintelligible | Assign `null` + flag issue |
| Valid data present | Extract as-is |


## HANDLING SPECIAL CASES

- **Confidence intervals** (e.g., "0.85 ± 0.02"): Extract main value only; no flagging needed
- **Ranges** (e.g., "0.75-0.90"): Assign `null`; flag issue
- **Formatted numbers** (e.g., "123.456K"): Extract as integer
- **Averages**: Do not create an entry for averages (e.g., "Average", "Avg.", etc.)
- **Multiple values** (e.g., "0.82, 0.85", "0.82/0.85"): Create separate entries with same row-level metadata, different `metric_value`; flag issue
- **Joining two columns**: Usually, the number of parameters and metric value are spread over two columns: Either the number of parameters is given per row or per task/entry in each row. In any case do not add the number of parameters as a separate entry. Instead, add it to the trained_parameters field for the respective metric values.

## NORMALIZING METRIC NAMES

Use the following canonical versions of the metric names (replace the alternative version by the canonical name in the output):

- accuracy: Often given as "acc", "Acc.", "ACC", "accuracy", etc.)
- Matthews correlation coefficient: Often given as "Matthews", "MCC", etc.)
- Pearson correlation coefficient: Often given as "pearson", "PMCC", "PCC")

If metric names are in column headers (e.g., 'SST-2 (Acc.)'), extract 'Acc.' and normalize to 'accuracy'.

## ISSUES TO FLAG

- Missing critical field
- Unintelligible data
- Range instead of single value
- Unclear field location (conflicting values)
- Alternatives without context
- Inconsistent data type
- Additional info missing

## OUTPUT FORMAT

```json
{{
  "entries": [
    {{
      "method": "string or null",
      "model": "string or null",
      "evaluation_task": "string or null",
      "finetuning_task": "string or null",
      "average_rank": "number or null",
      "trained_parameters": "number or null",
      "trained_parameter_ratio": "number or null",
      "metric_name": "string",
      "metric_value": "number or null",
      "note": "string or null"
    }}
  ],
  "issues": [
    "string including position in the table",
    "potentially multiple entries for multiple issues"
  ]
}}
```

---

# EXAMPLE 1

**Table:**
| Method | Model | SST-2 | CoNLL03 |
|--------|-------|----------|----------|
| Fine-tuning | BERT | 0.91 | 0.88 
| Fine-tuning | BERT | - | 0.92 |
| Prompt-tuning | GPT-3.5 | 0.87 ± 0.03 | 0.84 |

## Additional Info
Task: Named Entity Recognition (NER) and Part-of-Speech Tagging (POS)

## Output
```json
{{
  "entries": [
    {{ "method": "Fine-tuning", "model": "BERT", "evaluation_task": "SST-2", "metric_value": 0.91, "metric_name": null }},
    {{ "method": "Fine-tuning", "model": "BERT", "evaluation_task": "CoNLL03", "metric_value": 0.88, "metric_name": null }},
    {{ "method": "Fine-tuning", "model": "BERT", "evaluation_task": "CoNLL03", "metric_value": 0.92, "metric_name": null }},
    {{ "method": "Prompt-tuning", "model": "GPT-3.5", "evaluation_task": "SST-2", "metric_value": 0.87, "metric_name": null }},
    {{ "method": "Prompt-tuning", "model": "GPT-3.5", "evaluation_task": "CoNLL03", "metric_value": 0.84, "metric_name": null }}
  ],
  "issues": [
    "Missing value in row 2, column SST-2; assigned null.",
    "Average rank could not be derived.",
    "Metric names not specified."
  ]
}}
```

---

# EXAMPLE 2

**Table:**
| Method | Rank | #Params | SST-2 (Acc.) | CoNLL03 (F1) |
|--------|------|---------|--------------|--------------|
| LoRA | 16 | 0.21M | 0.91 | 0.88 
| AdaLoRA | 16 | 0.22M | 0.8 | 0.92 |
| EVA | 16 | 0.23M | 0.82 | 0.99 |

## Additional Info
Model: llama-7b, fine-tuned on train split of evaluation_task

## Output
```json
{{
  "entries": [
    {{ "method": "LoRA", "model": "llama-7b", "evaluation_task": "SST-2", "finetuning_task": "SST-2", "metric_name": "accuracy", "metric_value": 0.91, "trained_parameters": 21000000, "average_rank": 16}},
    {{ "method": "LoRA", "model": "llama-7b", "evaluation_task": "CoNLL03", "finetuning_task": "CoNLL03", "metric_name": "F1-score", "metric_value": 0.88, "trained_parameters": 21000000, "average_rank": 16 }},
    {{ "method": "AdaLoRA", "model": "llama-7b", "evaluation_task": "SST-2", "finetuning_task": "SST-2", "metric_name": "accuracy", "metric_value": 0.8, "trained_parameters": 22000000, "average_rank": 16 }},
    {{ "method": "AdaLoRA", "model": "llama-7b", "evaluation_task": "CoNLL03", "finetuning_task": "CoNLL03", "metric_name": "F1-score", "metric_value": 0.92, "trained_parameters": 22000000, "average_rank": 16 }},
    {{ "method": "EVA", "model": "llama-7b", "evaluation_task": "SST-2", "finetuning_task": "SST-2", "metric_name": "accuracy", "metric_value": 0.82, "trained_parameters": 23000000, "average_rank": 16 }},
    {{ "method": "EVA", "model": "llama-7b", "evaluation_task": "CoNLL03", "finetuning_task": "CoNLL03", "metric_name": "F1-score", "metric_value": 0.99, "trained_parameters": 23000000, "average_rank": 16 }}
  ],
  "issues": []
}}
```

---

# INPUT

## Additional Info
{info}
