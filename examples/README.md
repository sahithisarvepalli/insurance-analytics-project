# Examples & Learning Resources

This folder contains learning materials and reference code that complement the core
insurance analytics pipeline in `src/`.

## Structure

| Directory                       | Description                                                                                                                             |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| [concepts/](concepts/README.md) | 11 standalone Python learning modules covering argparse, CSV I/O, database connections, Pandas transforms, ML basics, logging, and more |
| [sas-python/](sas-python/)      | Side-by-side SAS ↔ Python translation examples for practitioners migrating from SAS                                                     |

## Running Examples

```bash
# Concepts — run any module directly
python examples/concepts/01_argparse_basics.py --name Alice --age 30
python examples/concepts/04_pandas_transform.py

# Tests embedded in concepts
python -m pytest examples/concepts/10_testing_basics.py -v
```

See each sub-folder's README for detailed instructions.
