"""
ui/toast.py
Toast popup notifications disabled per user request.
Retained as a clean no-op for backward compatibility.
"""

from __future__ import annotations


class Toast:
    """
    Toast popup notifications disabled per user request.
    No floating top-level popup windows are generated.
    """

    def __init__(
        self,
        parent=None,
        title: str = "",
        message: str = "",
        icon: str = "",
    ):
        pass
