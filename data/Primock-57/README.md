---
license: cc-by-4.0
language: en
pretty_name: Primock-57
size_categories:
  - n<100
---

# Primock-57

This is a version of the [Primock-57](https://github.com/babylonhealth/primock57) dataset converted to the [`sdialog`](https://github.com/idiap/sdialog) `Dialog` JSON format.  
It allows easy loading as dialog objects via `Dialog.from_file()` or `Dialog.from_huggingface`.

The dataset contains **57** simulated primary-care style consultations (doctor ↔ patient). Each dialog is stored as an individual JSON file and includes a sequence of turns labelled by speaker.

---
## How to use (Automatically, using `Dialog.from_huggingface()`)

Simply use the [`Dialog.from_huggingface()`](https://sdialog.readthedocs.io/en/latest/api/sdialog.html#sdialog.Dialog.from_huggingface) as in the following example:

```python
from sdialog import Dialog

primock57_dialogs = Dialog.from_huggingface("sdialog/Primock-57")

print("Number of dialogs:", len(primock57_dialogs))
```

---
## How to use (Manually, using `Dialog.from_file()`)

Alternatively, if you want to do it manually, you have to:

1. First, download the dataset from the Hugging Face Hub to a local directory (e.g., `"Primock-57"`):

```python
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="sdialog/Primock-57",
    repo_type="dataset",
    local_dir="Primock-57",
)
```

2. Then, load the dataset as `Dialog` objects:

```python
from sdialog import Dialog

primock57_dialogs = Dialog.from_file("Primock-57/")
print("Number of dialogs:", len(primock57_dialogs))

# Pretty-print the first dialog
primock57_dialogs[0].print()
```

You can also load an individual dialog by specifying its file path directly:

```python
from sdialog import Dialog

consultation01_dialog = Dialog.from_file("Primock-57/day1_consultation01_conversation.json")
consultation01_dialog.print()
```

## License

[Creative Commons Attribution 4.0 International (CC BY 4.0)](https://github.com/babylonhealth/primock57?tab=License-1-ov-file#readme)
