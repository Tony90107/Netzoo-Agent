"""Compatibility facade for workflow path safety."""

from .data.paths import condor_artifact_paths, resolved_output_collisions, validate_output_basename

__all__ = ["condor_artifact_paths", "resolved_output_collisions", "validate_output_basename"]
