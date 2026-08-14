### Installing the correct dependencies


- Create environment using `uv`: `uv venv`
- Manually install the correct torch version.
- Install the other dependencies: `uv pip install -c constraints.txt -r requirements.txt` 
- Lock dependencies: `uv lock`




### Evaluation Example

```bash
uv run --locked  extract.py
```
