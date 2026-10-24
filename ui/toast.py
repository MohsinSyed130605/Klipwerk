"""Notification toast component interface."""

from __future__ import annotations


class Toast:

    def __init__(
        self,
        parent=None,
        title: str = "",
        message: str = "",
        icon: str = "",
    ):
        pass
