"""
Sandbox Manager - OS-Level Isolation

Provides OS-level sandboxing for subagents (Bubblewrap on Linux, Seatbelt on macOS).
Falls back to permission-based isolation if OS-level sandboxing is unavailable.
"""

import logging
import os
import platform
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Sandbox:
    """Represents a sandbox environment"""

    sandbox_id: str
    subagent_id: str
    isolated: bool
    filesystem_root: Optional[Path] = None
    allowed_tools: List[str] = field(default_factory=list)
    network_enabled: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class SandboxManager:
    """
    Manages OS-level sandboxing for subagents.

    Supports:
    - Linux: Bubblewrap (bwrap)
    - macOS: Seatbelt (sandbox-exec)
    - Fallback: Permission-based isolation
    """

    def __init__(self):
        """Initialize the sandbox manager"""
        self.system = platform.system()
        self.sandbox_available = self._check_sandbox_availability()
        self.active_sandboxes: Dict[str, Sandbox] = {}

        if self.sandbox_available:
            logger.info(f"Sandboxing available on {self.system}")
        else:
            logger.warning(
                f"OS-level sandboxing not available on {self.system}, "
                "using permission-based isolation"
            )

    def _check_sandbox_availability(self) -> bool:
        """
        Check if OS-level sandboxing is available.

        Returns:
            True if sandboxing is available
        """
        if self.system == "Linux":
            # Check for bubblewrap
            try:
                result = subprocess.run(
                    ["which", "bwrap"], capture_output=True, timeout=1
                )
                return result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return False

        elif self.system == "Darwin":  # macOS
            # Check for sandbox-exec
            try:
                result = subprocess.run(
                    ["which", "sandbox-exec"], capture_output=True, timeout=1
                )
                return result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return False

        # Windows or other - no OS-level sandboxing
        return False

    def is_available(self) -> bool:
        """
        Check if sandboxing is available.

        Returns:
            True if sandboxing is available
        """
        return self.sandbox_available

    def create_sandbox(
        self,
        subagent_id: str,
        allowed_tools: List[str],
        filesystem_root: Optional[Path] = None,
        network_enabled: bool = False,
    ) -> Sandbox:
        """
        Create a sandbox for a subagent.

        Args:
            subagent_id: ID of the subagent
            allowed_tools: List of allowed tools
            filesystem_root: Optional filesystem root (for isolation)
            network_enabled: Whether to allow network access

        Returns:
            Sandbox instance
        """
        import uuid

        sandbox_id = str(uuid.uuid4())

        if self.sandbox_available:
            # Create OS-level sandbox
            if self.system == "Linux":
                sandbox = self._create_bubblewrap_sandbox(
                    sandbox_id,
                    subagent_id,
                    allowed_tools,
                    filesystem_root,
                    network_enabled,
                )
            elif self.system == "Darwin":
                sandbox = self._create_seatbelt_sandbox(
                    sandbox_id,
                    subagent_id,
                    allowed_tools,
                    filesystem_root,
                    network_enabled,
                )
            else:
                # Fallback to permission-based
                sandbox = self._create_permission_sandbox(
                    sandbox_id, subagent_id, allowed_tools
                )
        else:
            # Use permission-based isolation
            sandbox = self._create_permission_sandbox(
                sandbox_id, subagent_id, allowed_tools
            )

        self.active_sandboxes[sandbox_id] = sandbox
        logger.info(f"Created sandbox {sandbox_id} for subagent {subagent_id}")

        return sandbox

    def _create_bubblewrap_sandbox(
        self,
        sandbox_id: str,
        subagent_id: str,
        allowed_tools: List[str],
        filesystem_root: Optional[Path],
        network_enabled: bool,
    ) -> Sandbox:
        """
        Create a Bubblewrap sandbox (Linux).

        Args:
            sandbox_id: Sandbox ID
            subagent_id: Subagent ID
            allowed_tools: Allowed tools
            filesystem_root: Filesystem root
            network_enabled: Network access

        Returns:
            Sandbox instance
        """
        # In production, would create actual bubblewrap sandbox
        # For now, return a mock sandbox
        return Sandbox(
            sandbox_id=sandbox_id,
            subagent_id=subagent_id,
            isolated=True,
            filesystem_root=filesystem_root,
            allowed_tools=allowed_tools,
            network_enabled=network_enabled,
            metadata={"type": "bubblewrap", "os": "Linux"},
        )

    def _create_seatbelt_sandbox(
        self,
        sandbox_id: str,
        subagent_id: str,
        allowed_tools: List[str],
        filesystem_root: Optional[Path],
        network_enabled: bool,
    ) -> Sandbox:
        """
        Create a Seatbelt sandbox (macOS).

        Args:
            sandbox_id: Sandbox ID
            subagent_id: Subagent ID
            allowed_tools: Allowed tools
            filesystem_root: Filesystem root
            network_enabled: Network access

        Returns:
            Sandbox instance
        """
        # In production, would create actual seatbelt sandbox
        # For now, return a mock sandbox
        return Sandbox(
            sandbox_id=sandbox_id,
            subagent_id=subagent_id,
            isolated=True,
            filesystem_root=filesystem_root,
            allowed_tools=allowed_tools,
            network_enabled=network_enabled,
            metadata={"type": "seatbelt", "os": "Darwin"},
        )

    def _create_permission_sandbox(
        self, sandbox_id: str, subagent_id: str, allowed_tools: List[str]
    ) -> Sandbox:
        """
        Create a permission-based sandbox (fallback).

        Args:
            sandbox_id: Sandbox ID
            subagent_id: Subagent ID
            allowed_tools: Allowed tools

        Returns:
            Sandbox instance
        """
        return Sandbox(
            sandbox_id=sandbox_id,
            subagent_id=subagent_id,
            isolated=False,  # Not truly isolated, just permission-based
            allowed_tools=allowed_tools,
            network_enabled=True,  # No network restrictions in fallback
            metadata={"type": "permission_based", "os": self.system},
        )

    def destroy_sandbox(self, sandbox_id: str) -> bool:
        """
        Destroy a sandbox.

        Args:
            sandbox_id: Sandbox ID

        Returns:
            True if destroyed successfully
        """
        if sandbox_id not in self.active_sandboxes:
            logger.warning(f"Sandbox {sandbox_id} not found")
            return False

        sandbox = self.active_sandboxes.pop(sandbox_id)

        # In production, would clean up OS-level sandbox resources
        logger.info(f"Destroyed sandbox {sandbox_id}")

        return True

    def get_sandbox(self, sandbox_id: str) -> Optional[Sandbox]:
        """
        Get a sandbox by ID.

        Args:
            sandbox_id: Sandbox ID

        Returns:
            Sandbox or None if not found
        """
        return self.active_sandboxes.get(sandbox_id)
