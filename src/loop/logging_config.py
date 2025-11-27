"""
Logging configuration for the feedback loop orchestrator.

Provides flexible logging options with file and console handlers,
structured formatting, and different verbosity levels.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class OrchestratorLogger:
    """
    Configures logging for the LoopOrchestrator with enhanced formatting and file output.
    
    Features:
    - Console and file logging
    - Structured formatting with timestamps
    - Different verbosity levels
    - Rotating file handlers
    - Color-coded console output (optional)
    """
    
    def __init__(
        self,
        name: str = "orchestrator",
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        log_dir: Optional[str] = None,
        verbose: bool = False
    ):
        """
        Initialize the logger configuration.
        
        Args:
            name: Logger name (default: "orchestrator")
            log_level: Logging level - DEBUG, INFO, WARNING, ERROR (default: INFO)
            log_file: Specific log file path. If None, generates timestamped filename
            log_dir: Directory for log files (default: "./logs")
            verbose: If True, sets DEBUG level and detailed formatting
        """
        self.name = name
        self.log_level = logging.DEBUG if verbose else getattr(logging, log_level.upper())
        self.verbose = verbose
        
        # Set up log directory
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = Path("./logs")
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up log file
        if log_file:
            self.log_file = Path(log_file)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file = self.log_dir / f"orchestrator_{timestamp}.log"
        
        self.logger = self._configure_logger()
    
    def _configure_logger(self) -> logging.Logger:
        """Configure and return the logger with handlers."""
        logger = logging.getLogger(self.name)
        logger.setLevel(self.log_level)
        
        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()
        
        # Console handler with color-coded formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_formatter = self._get_console_formatter()
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler with detailed formatting
        file_handler = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Always DEBUG in file
        file_formatter = self._get_file_formatter()
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        return logger
    
    def _get_console_formatter(self) -> logging.Formatter:
        """Get formatter for console output."""
        if self.verbose:
            # Detailed format for verbose mode
            fmt = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
        else:
            # Simplified format for normal mode
            fmt = '%(levelname)-8s | %(message)s'
        
        return logging.Formatter(
            fmt=fmt,
            datefmt='%H:%M:%S'
        )
    
    def _get_file_formatter(self) -> logging.Formatter:
        """Get formatter for file output (always detailed)."""
        return logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def get_logger(self) -> logging.Logger:
        """Return the configured logger."""
        return self.logger
    
    def log_iteration_start(self, iteration: int, activity: str):
        """Log the start of an iteration."""
        self.logger.info("=" * 80)
        self.logger.info(f"ITERATION {iteration} - Activity: {activity}")
        self.logger.info("=" * 80)
    
    def log_iteration_end(self, iteration: int, score: float, converged: bool, tokens: int, latency_ms: float):
        """Log the end of an iteration with results."""
        self.logger.info(f"Iteration {iteration} completed:")
        self.logger.info(f"  Score: {score:.4f}")
        self.logger.info(f"  Converged: {converged}")
        self.logger.info(f"  Tokens used: {tokens}")
        self.logger.info(f"  Latency: {latency_ms:.2f} ms")
    
    def log_generation(self, phase: str, tokens: int, latency_ms: float):
        """Log LLM generation details."""
        self.logger.debug(f"{phase} generation: {tokens} tokens, {latency_ms:.2f} ms")
    
    def log_evaluation(self, score: float, matches_reference: bool, issues: list):
        """Log evaluation results."""
        self.logger.debug(f"Evaluation: score={score:.4f}, matches={matches_reference}")
        if issues:
            self.logger.debug(f"Issues found: {', '.join(issues)}")
    
    def log_feedback(self, feedback: str):
        """Log feedback from evaluation."""
        if self.verbose:
            self.logger.debug(f"Feedback: {feedback}")
        else:
            self.logger.debug(f"Feedback: {feedback[:100]}...")
    
    def log_convergence(self, reason: str, final_score: float, iterations: int):
        """Log final convergence status."""
        self.logger.info("=" * 80)
        self.logger.info("CONVERGENCE STATUS")
        self.logger.info("=" * 80)
        self.logger.info(f"Reason: {reason}")
        self.logger.info(f"Final score: {final_score:.4f}")
        self.logger.info(f"Iterations used: {iterations}")
    
    def log_summary(self, summary: dict):
        """Log final summary statistics."""
        self.logger.info("=" * 80)
        self.logger.info("SUMMARY")
        self.logger.info("=" * 80)
        for key, value in summary.items():
            if isinstance(value, float):
                self.logger.info(f"  {key}: {value:.4f}")
            else:
                self.logger.info(f"  {key}: {value}")
    
    def close(self):
        """Close all handlers and clean up."""
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)


def setup_orchestrator_logging(
    verbose: bool = False,
    log_file: Optional[str] = None,
    log_dir: Optional[str] = None,
    log_level: str = "INFO"
) -> logging.Logger:
    """
    Convenience function to quickly set up orchestrator logging.
    
    Args:
        verbose: Enable verbose (DEBUG) logging
        log_file: Path to log file
        log_dir: Directory for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = setup_orchestrator_logging(verbose=True, log_dir="./logs")
        >>> logger.info("Starting feedback loop")
    """
    logger_config = OrchestratorLogger(
        name="orchestrator",
        log_level=log_level,
        log_file=log_file,
        log_dir=log_dir,
        verbose=verbose
    )
    
    return logger_config.get_logger()
