"""Compatibility facade for generated artifact validation."""

from .data.artifacts import ARTIFACT_WRITE_ACTIONS, validate_output_artifacts

__all__ = ["ARTIFACT_WRITE_ACTIONS", "validate_output_artifacts"]
