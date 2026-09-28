"""src/common/exceptions.py - custom exception hierarchy for the pipeline."""


class PipelineError(Exception):
    """
    Base class for every error this project raises on purpose.

    `context` carries structured details (batch id, row counts, table name)
    so logs and the orchestrator can report *what* failed, not just a message.
    """

    def __init__(self, message: str, **context):
        super().__init__(message)
        self.message = message
        self.context = context

    def __str__(self) -> str:
        if not self.context:
            return self.message
        details = ", ".join(f"{k}={v}" for k, v in self.context.items())
        return f"{self.message} [{details}]"


class ConfigurationError(PipelineError):
    """Config or credentials missing/invalid."""


class BronzeIngestionError(PipelineError):
    """Raw load failed (unreadable file, empty input, failed row-count check)."""


class SchemaMismatchError(PipelineError):
    """Incoming columns/types don't match the expected schema."""


class SilverValidationError(PipelineError):
    """Cleaning or validation failed beyond what quarantine can absorb."""


class GoldAggregationError(PipelineError):
    """Aggregation or reconciliation failed in the gold layer."""


class ExportError(PipelineError):
    """Writing to an external system (OCI, S3, Autonomous DB) failed."""


if __name__ == "__main__":
    try:
        raise BronzeIngestionError(
            "Row count mismatch", batch_id="BATCH_20260821", expected=136, actual=130
        )
    except PipelineError as err:
        print("Caught as base class:", err)
        print("Type:", type(err).__name__)
        print("Context dict:", err.context)

        print(
            "Is SchemaMismatchError a PipelineError?",
            issubclass(SchemaMismatchError, PipelineError),
        )
        print("No-context message:", ConfigurationError("Missing OCI namespace"))
