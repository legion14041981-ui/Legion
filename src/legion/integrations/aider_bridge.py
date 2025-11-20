"""AiderBridge - Asynchronous bridge for Aider CLI integration with Legion agents."""

import subprocess
import threading
import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class AiderBridge:
    """Manages interactive communication with Aider CLI through stdin/stdout pipes."""

    def __init__(self, repo_path: str = r"C:\Legion", model: str = "openrouter/deepseek/deepseek-r1:free"):
        """Initialize AiderBridge.
        
        Args:
            repo_path: Path to Legion repository directory
            model: LLM model to use (default: openrouter free DeepSeek)
        """
        self.repo_path = repo_path
        self.model = model
        self.proc = None
        self.lock = threading.Lock()
        self.is_running = False
        self.callbacks: Dict[str, Callable] = {}
        self.session_id = datetime.now().isoformat()

    def start(self) -> bool:
        """Start Aider subprocess in interactive mode."""
        if self.is_running:
            logger.warning("AiderBridge already running")
            return False
        
        try:
            self.proc = subprocess.Popen(
                ["aider", "--model", self.model],
                cwd=self.repo_path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True,
                bufsize=1
            )
            self.is_running = True
            logger.info(f"AiderBridge started (session: {self.session_id})")
            return True
        except Exception as e:
            logger.error(f"Failed to start AiderBridge: {str(e)}")
            self.is_running = False
            return False

    def send_command(self, command: str, timeout: int = 60) -> Optional[str]:
        """Send command to Aider and receive response.
        
        Args:
            command: Command or question for Aider
            timeout: Response timeout in seconds
            
        Returns:
            Aider response or None if failed
        """
        if not self.is_running or not self.proc:
            logger.error("AiderBridge not running")
            return None
        
        with self.lock:
            try:
                self.proc.stdin.write(command + "\n")
                self.proc.stdin.flush()
                
                output = ""
                while True:
                    line = self.proc.stdout.readline()
                    if not line:
                        break
                    output += line
                    if "> " in line:  # Aider prompt
                        break
                
                logger.info(f"Command executed: {command[:50]}...")
                return output.strip()
            except Exception as e:
                logger.error(f"Error sending command: {str(e)}")
                return None

    def send_batch(self, commands: list) -> Dict[str, str]:
        """Send multiple commands sequentially.
        
        Args:
            commands: List of commands to execute
            
        Returns:
            Dictionary mapping commands to responses
        """
        results = {}
        for cmd in commands:
            response = self.send_command(cmd)
            results[cmd] = response if response else "[No response]"
        return results

    def register_callback(self, event: str, callback: Callable) -> None:
        """Register callback for events.
        
        Args:
            event: Event name (e.g., 'on_task_complete', 'on_error')
            callback: Callable to execute
        """
        self.callbacks[event] = callback
        logger.info(f"Callback registered for event: {event}")

    def trigger_callback(self, event: str, data: Any) -> None:
        """Trigger registered callback.
        
        Args:
            event: Event name
            data: Data to pass to callback
        """
        if event in self.callbacks:
            try:
                self.callbacks[event](data)
            except Exception as e:
                logger.error(f"Callback error for {event}: {str(e)}")

    def close(self) -> None:
        """Close AiderBridge connection."""
        if self.proc and self.is_running:
            try:
                self.proc.stdin.write("exit\n")
                self.proc.stdin.flush()
                self.proc.terminate()
                self.is_running = False
                logger.info("AiderBridge closed")
            except Exception as e:
                logger.error(f"Error closing AiderBridge: {str(e)}")

    def get_status(self) -> Dict[str, Any]:
        """Get current bridge status.
        
        Returns:
            Status dictionary
        """
        return {
            "is_running": self.is_running,
            "repo_path": self.repo_path,
            "model": self.model,
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat()
        }

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
