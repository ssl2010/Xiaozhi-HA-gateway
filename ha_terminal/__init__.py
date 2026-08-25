"""Deterministic Home Assistant command handling for the Xiaozhi terminal."""

from .intent_parser import Command, parse_commands

__all__ = ["Command", "parse_commands"]
