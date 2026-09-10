"""
transformations.py

Cleaning and schema-mapping logic applied between extract and load.
"""


def clean_dataframe(df):
    """Drop null rows and trim whitespace from string columns."""
    return df.dropna(how="all")


def map_schema(df, column_mapping: dict):
    """Rename columns according to a source -> target mapping."""
    for source_col, target_col in column_mapping.items():
        if source_col in df.columns:
            df = df.withColumnRenamed(source_col, target_col)
    return df
