"""Base of every error `skillctl` reports to the user as a one-line message."""


class SkillctlError(Exception):
    """An expected failure whose message is written for the user, not a developer."""
