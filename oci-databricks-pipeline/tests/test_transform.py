"""Tests for src/transform/transformations.py"""

from src.transform.transformations import map_schema


def test_map_schema_renames_columns():
    class FakeDF:
        def __init__(self, columns):
            self.columns = columns
            self.renamed = []

        def withColumnRenamed(self, old, new):
            self.renamed.append((old, new))
            self.columns = [new if c == old else c for c in self.columns]
            return self

    df = FakeDF(columns=["src_col"])
    result = map_schema(df, {"src_col": "target_col"})
    assert "target_col" in result.columns
