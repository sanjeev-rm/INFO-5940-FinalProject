"""
Session Management

Handles user sessions, conversation state, and session persistence.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import uuid

class SessionManager:
    """Manages user sessions and conversation state"""

    def __init__(self, config=None):
        """
        Initialize session manager

        Args:
            config: Application configuration (optional)
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Create sessions directory
        self.sessions_dir = Path("data/sessions")
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        # Active sessions in memory
        self.active_sessions = {}

        # Session timeout (default 1 hour)
        self.session_timeout = timedelta(
            minutes=config.SESSION_TIMEOUT_MINUTES if config else 60
        )

    @staticmethod
    def generate_session_id() -> str:
        """
        Generate a unique session ID

        Returns:
            str: Unique session identifier
        """
        return str(uuid.uuid4())[:12]  # Use first 12 chars for readability

    def create_session(self, session_id: str = None) -> str:
        """
        Create a new session

        Args:
            session_id: Optional custom session ID

        Returns:
            str: Session ID
        """
        if not session_id:
            session_id = self.generate_session_id()

        session_data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "messages": [],
            "user_info": {},
            "session_stats": {
                "total_messages": 0,
                "guest_messages": 0,
                "agent_messages": 0,
                "coaching_interactions": 0
            },
            "training_metadata": {
                "scenario_type": None,
                "difficulty_level": "beginner",
                "learning_objectives": []
            },
            "status": "active"
        }

        # Store in memory and save to disk
        self.active_sessions[session_id] = session_data
        self._save_session(session_id, session_data)

        self.logger.info(f"Created new session: {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data

        Args:
            session_id: Session identifier

        Returns:
            Session data or None if not found
        """
        # Check if session is in memory
        if session_id in self.active_sessions:
            session_data = self.active_sessions[session_id]
        else:
            # Try to load from disk
            session_data = self._load_session(session_id)
            if session_data:
                self.active_sessions[session_id] = session_data

        if not session_data:
            return None

        # Check if session has expired
        if self._is_session_expired(session_data):
            self.end_session(session_id)
            return None

        return session_data

    def update_session(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update session data

        Args:
            session_id: Session identifier
            update_data: Data to update

        Returns:
            bool: Success status
        """
        session_data = self.get_session(session_id)
        if not session_data:
            self.logger.warning(f"Attempted to update non-existent session: {session_id}")
            return False

        # Update last activity
        session_data["last_activity"] = datetime.now().isoformat()

        # Merge update data
        for key, value in update_data.items():
            if key in session_data:
                if isinstance(session_data[key], dict) and isinstance(value, dict):
                    session_data[key].update(value)
                elif isinstance(session_data[key], list) and isinstance(value, list):
                    session_data[key].extend(value)
                else:
                    session_data[key] = value
            else:
                session_data[key] = value

        # Save updated session
        self._save_session(session_id, session_data)
        return True

    def add_message(self, session_id: str, message: Dict[str, Any]) -> bool:
        """
        Add a message to the session

        Args:
            session_id: Session identifier
            message: Message data

        Returns:
            bool: Success status
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return False

        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()

        # Add message to session
        session_data["messages"].append(message)

        # Update statistics
        session_data["session_stats"]["total_messages"] += 1
        if message.get("role") == "guest":
            session_data["session_stats"]["guest_messages"] += 1
        elif message.get("role") == "agent":
            session_data["session_stats"]["agent_messages"] += 1

        # Limit message history if configured
        max_messages = self.config.MAX_MESSAGE_HISTORY if self.config else 100
        if len(session_data["messages"]) > max_messages:
            # Keep the most recent messages
            session_data["messages"] = session_data["messages"][-max_messages:]

        # Update session
        return self.update_session(session_id, session_data)

    def get_messages(self, session_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get messages from a session

        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return

        Returns:
            List of messages
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return []

        messages = session_data.get("messages", [])

        if limit and len(messages) > limit:
            return messages[-limit:]

        return messages

    def end_session(self, session_id: str) -> bool:
        """
        End a session

        Args:
            session_id: Session identifier

        Returns:
            bool: Success status
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return False

        # Update session status
        session_data["status"] = "ended"
        session_data["ended_at"] = datetime.now().isoformat()

        # Calculate session duration
        created_at = datetime.fromisoformat(session_data["created_at"])
        ended_at = datetime.now()
        duration = (ended_at - created_at).total_seconds()
        session_data["duration_seconds"] = duration

        # Save final session state
        self._save_session(session_id, session_data)

        # Remove from active sessions
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

        self.logger.info(f"Ended session: {session_id} (duration: {duration:.1f}s)")
        return True

    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions

        Returns:
            int: Number of sessions cleaned up
        """
        cleaned_count = 0

        # Check active sessions
        expired_sessions = []
        for session_id, session_data in self.active_sessions.items():
            if self._is_session_expired(session_data):
                expired_sessions.append(session_id)

        # End expired sessions
        for session_id in expired_sessions:
            if self.end_session(session_id):
                cleaned_count += 1

        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} expired sessions")

        return cleaned_count

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get session statistics

        Args:
            session_id: Session identifier

        Returns:
            Dictionary containing session statistics
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return {}

        stats = session_data.get("session_stats", {}).copy()

        # Add calculated statistics
        created_at = datetime.fromisoformat(session_data["created_at"])
        last_activity = datetime.fromisoformat(session_data["last_activity"])

        stats.update({
            "session_age_minutes": (datetime.now() - created_at).total_seconds() / 60,
            "inactive_minutes": (datetime.now() - last_activity).total_seconds() / 60,
            "status": session_data.get("status", "unknown"),
            "message_count": len(session_data.get("messages", []))
        })

        return stats

    def _save_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """
        Save session data to disk

        Args:
            session_id: Session identifier
            session_data: Session data to save

        Returns:
            bool: Success status
        """
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, default=str)
            return True

        except Exception as e:
            self.logger.error(f"Failed to save session {session_id}: {e}")
            return False

    def _load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load session data from disk

        Args:
            session_id: Session identifier

        Returns:
            Session data or None if not found
        """
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            if not session_file.exists():
                return None

            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            return session_data

        except Exception as e:
            self.logger.error(f"Failed to load session {session_id}: {e}")
            return None

    def _is_session_expired(self, session_data: Dict[str, Any]) -> bool:
        """
        Check if a session has expired

        Args:
            session_data: Session data

        Returns:
            bool: True if expired
        """
        try:
            last_activity = datetime.fromisoformat(session_data["last_activity"])
            return datetime.now() - last_activity > self.session_timeout

        except (KeyError, ValueError):
            # If we can't determine last activity, consider it expired
            return True

    def list_sessions(self, include_ended: bool = False) -> List[Dict[str, Any]]:
        """
        List all sessions

        Args:
            include_ended: Include ended sessions

        Returns:
            List of session summaries
        """
        sessions = []

        # Get sessions from memory
        for session_id, session_data in self.active_sessions.items():
            if session_data.get("status") != "ended" or include_ended:
                sessions.append({
                    "session_id": session_id,
                    "created_at": session_data.get("created_at"),
                    "status": session_data.get("status", "active"),
                    "message_count": len(session_data.get("messages", []))
                })

        # Also check disk for sessions not in memory
        for session_file in self.sessions_dir.glob("*.json"):
            session_id = session_file.stem
            if session_id not in self.active_sessions:
                session_data = self._load_session(session_id)
                if session_data and (session_data.get("status") != "ended" or include_ended):
                    sessions.append({
                        "session_id": session_id,
                        "created_at": session_data.get("created_at"),
                        "status": session_data.get("status", "active"),
                        "message_count": len(session_data.get("messages", []))
                    })

        return sorted(sessions, key=lambda x: x["created_at"], reverse=True)