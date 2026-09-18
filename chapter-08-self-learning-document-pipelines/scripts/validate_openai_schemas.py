from _common import ROOT
from src.documents.contracts import required_fields
from src.planner.schemas import FIELD_SCHEMAS, extraction_response_schema, validate_strict_schema


def main():
    checked = 0
    for version in ("V1", "V2"):
        for family in FIELD_SCHEMAS:
            schema = extraction_response_schema(family, required_fields(family, version))
            validate_strict_schema(schema)
            checked += 1
            print(f"PASS {version} {family}")
    print(f"\nValidated {checked} strict Structured Outputs schemas locally. No API call was made.")


if __name__ == "__main__":
    main()
