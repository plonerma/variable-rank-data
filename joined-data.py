# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "matplotlib==3.11.1",
#     "pandas==3.0.5",
#     "pydantic==2.13.4",
#     "seaborn==0.13.2",
# ]
# ///

import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from pathlib import Path
    import json
    import pandas as pd
    from collections import defaultdict
    import yaml
    import numpy as np
    import matplotlib.pyplot as plt

    from model import ResultEntryModel

    import seaborn as sns

    return Path, ResultEntryModel, json, mo, pd, plt, sns, yaml


@app.cell
def _(mo):
    mo.md(r"""
    ## Save prompt for inclusion in paper
    """)
    return


@app.cell
def _(ResultEntryModel):
    def _():
        field_descriptions = ResultEntryModel.fields_description_text()
        field_names = ", ".join(ResultEntryModel.model_fields)

        with open("score_extraction_prompt.md") as f:
            prompt = f.read().format(field_descriptions=field_descriptions, field_names=field_names, info="<ANNOTATION TEXT>")
        with open("/home/max/Documents/Papers/2026/variable-rank/extraction-prompt.txt", "w") as f:
            f.write(prompt)

        return

    _()
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Data Cleaning
    """)
    return


@app.cell
def _(Path, json):
    table_map = {}

    for _p in Path("data/papers").glob("*.json"):
        with open(_p) as _f:
            _paper_data = json.load(_f)

        for _a in _paper_data["annotations"]:
            assert _a["key"] not in table_map
            table_map[_a["key"]] = _p.stem
    return (table_map,)


@app.cell
def _(Path, json, pd, table_map):
    results_path = Path("data/scores/")

    frames = []

    for p in results_path.glob("*.json"):
        try:
            with p.open() as f:
                data = json.load(f)

            df = pd.DataFrame.from_records(data["entries"])
            df["tableKey"] = p.stem
            df["paperKey"] = table_map[p.stem]
        except ValueError as e:
            print(e)

        frames.append(df)

    df = pd.concat(frames, ignore_index=True)
    df
    return (df,)


@app.cell
def _(yaml):
    with open("normalization/model_names.yaml") as _f:
        model_names = yaml.safe_load(_f)

    with open("normalization/task_names.yaml") as _f:
        task_names = yaml.safe_load(_f)

    def get_slug(name):
        if not isinstance(name, str):
            return None
        else:
            return name.lower().replace(" ", "").replace("_", "").replace("-", "")
    return get_slug, model_names, task_names


@app.cell
def _(df, get_slug, model_names, pd, task_names):
    invalid_model = df.model.map(get_slug).isin(model_names["invalid"]) | df.model.isna()
    invalid_task = df.evaluation_task.map(get_slug).isin(task_names["invalid"]) | df.evaluation_task.isna()

    removed_models = df.model[invalid_model].unique()
    removed_tasks = df.evaluation_task[invalid_task].unique()


    df_clean = df[~(invalid_model | invalid_task)]

    print(removed_models)

    print("Removing models (unspecific names):", ", ".join(m  if m is not None and not pd.isna(m) else "-" for m in removed_models))
    print("Removing tasks (unspecific names):", ", ".join(t if t is not None and not pd.isna(t) else "-" for t in removed_tasks))


    df_clean.model = df_clean.model.map(lambda n: model_names["canonical"].get(get_slug(n), n))
    df_clean.evaluation_task = df_clean.evaluation_task.map(lambda n: task_names["canonical"].get(get_slug(n), n))
    df_clean.finetuning_task = df_clean.finetuning_task.map(lambda n: task_names["canonical"].get(get_slug(n), n))


    print("Remaining models:", ", ".join(df_clean.model.unique()))
    print("Remaining evaluation tasks:", ", ".join(df_clean.evaluation_task.unique()))

    df_clean
    return (df_clean,)


@app.cell
def _(df_clean, plt, sns):
    combination_counts = df_clean.groupby(["model", "evaluation_task"]).paperKey.nunique()

    combination_counts = combination_counts[combination_counts>1]
    combination_counts = combination_counts.unstack(level=0)

    combination_counts

    # Sort both rows (by row sum) and columns (by column sum)
    #row_order = combination_counts.sum(axis=1).sort_values(ascending=False).index
    _row_order = [
        'SST-2', 'QNLI', 'CoLA', 'MRPC', 'MNLI', 'QQP', 'RTE', 'STS-B', 'SQuADv1.1', 'SQuADv2.0',
        'ARC-e', 'ARC-c',
        'PIQA', 'OpenBookQA', 'BoolQ', 'HellaSwag', 'WinoGrande',
        'SIQA', 'GSM8k', 'XSum', 'CNN/DailyMail',
        'HumanEval', 'MTBench', 'Cifar 100'
    ]

    assert set(_row_order) == set(combination_counts.index)

    #_col_order = combination_counts.sum().sort_values(ascending=False).index

    _col_order = [
        'DeBERTaV3-base', 'RoBERTa-base', 'RoBERTa-large', 'T5-base',
        'LLaMA-7B', 'LLaMA-3-8B', 'ChatGPT',
        'LLaMA-2-7B', 'LLaMA-13B', 'BART-large',
        'LLaMA-3.1-8B-Base', 'LLaMA-3.1-8B', 'BART-base', 'ViT-B16']

    assert set(_col_order) == set(combination_counts.columns)

    combination_counts = combination_counts.loc[_row_order, _col_order]
    combination_counts

    _fig, _ax = plt.subplots(figsize=(4, 6))

    sns.heatmap(combination_counts, cmap="Greens", annot=True, ax=_ax, cbar=False)
    _ax.set_ylabel("Evaluation Task")
    _ax.set_xlabel("Base Model")

    _fig.tight_layout()
    _fig.savefig("plots/eval_settings.pdf")

    _ax


    return


@app.cell
def _(df_clean):


    for _m in sorted(df_clean.method.unique()):
        print(_m)
    return


@app.cell
def _(df_clean, sns):
    _task = "SST-2"
    _data = df_clean[
        (df_clean.evaluation_task == _task)
        & (df_clean.model == "DeBERTaV3-base")
    ]

    ax = sns.scatterplot(data=_data, x="trained_parameters", y="metric_value")
    ax.set_xscale("log")
    ax.set_ylim([92, 97])
    ax
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
