from vllm import LLM, SamplingParams, EngineArgs
from vllm.sampling_params import StructuredOutputsParams
from PIL import Image
from pathlib import Path

from model import result_schema as json_schema, ResultEntryModel


MODEL_NAME = "Qwen/Qwen3-VL-8B-Instruct"
PROMPT_TEMPLATE = (
    "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n"
    "<|im_start|>user\n<|vision_start|><|image_pad|><|vision_end|>"
    "{question}<|im_end|>\n"
    "<|im_start|>assistant\n"
)

with open("score_extraction_prompt.md") as f:
    PROMPT = f.read().strip()


field_description = ResultEntryModel.fields_description_text()
field_names = ", ".join(ResultEntryModel.model_fields)



print("Preparing inputs")
print("Using the following prompt:\n")
print(PROMPT.format(info="<additional info from extraction>", field_descriptions=field_description, field_names=field_names))
print("---")

inputs = []
input_ids = []
target_paths = []

for image_path in Path("./data/tables").glob("*.png"):
    input_id = image_path.stem

    target_path = Path(f"./data/scores/{input_id}.json")

    if target_path.exists():
        print(f"Skipping {input_id} ({target_path} exists).")
        continue


    # loading image
    image = Image.open(image_path).convert("RGB")


    with open(Path("./extractions") / f"{input_id}.txt") as f:
        info = f.read()

    prompt = PROMPT_TEMPLATE.format(question=PROMPT.format(info=info, field_descriptions=field_description, field_names=field_names))


    input_ids.append(input_id)
    target_paths.append(target_path)
    inputs.append(
        {
            "prompt": prompt,
            "multi_modal_data": {
                "image": image
            },
        }
    )

if len(inputs) > 0:
    print("Loading model")

    engine_args = EngineArgs(
        model=MODEL_NAME,
        max_model_len=100_000,
        mm_processor_kwargs={
            "min_pixels": 28 * 28,
            "max_pixels": 1280 * 28 * 28,
            "fps": 1,
        },
        limit_mm_per_prompt={"image": 1},
    )

    llm = LLM.from_engine_args(engine_args)


    sampling_params = SamplingParams(
        temperature=0.1,
        max_tokens=100_000,
        stop_token_ids=None,
        structured_outputs=StructuredOutputsParams(
            json=json_schema,
        ),
    )



    print("Processing inputs")
    outputs = llm.generate(inputs, sampling_params=sampling_params)

    print("Storing results")

    for target_path, result in zip(target_paths, outputs, strict=True):

        response = result.outputs[0].text

        with open(target_path, "w") as f:
            f.write(response)

else:
    print("No inputs to process.")

print("Done.")
