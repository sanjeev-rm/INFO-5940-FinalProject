"""
Report Agent

Generates comprehensive session reports and summaries for training purposes.
Creates detailed analysis for both employees and managers.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from .base_agent import BaseAgent
from rag_system.retriever import RAGRetriever

class ReportAgent(BaseAgent):
    """AI agent that generates training session reports and summaries"""

    def __init__(self, config, rag_retriever: RAGRetriever):
        super().__init__(config, model_preference="smart")
        self.rag_retriever = rag_retriever

    def get_system_prompt(self) -> str:
        """Get system prompt for report agent"""
        return """
        You are an expert training analyst specializing in hotel guest service evaluation.
        Your role is to create comprehensive, constructive training reports that help both employees and managers.

        REPORT PRINCIPLES:
        - Be objective and constructive
        - Provide specific examples from the conversation
        - Reference training standards when relevant
        - Include both strengths and development areas
        - Offer concrete suggestions for improvement
        - Structure reports for easy reading and action

        REPORT SECTIONS TO INCLUDE:
        1. Executive Summary
        2. Scenario Overview
        3. Performance Highlights (what went well)
        4. Development Opportunities (areas for improvement)
        5. Training Recommendations
        6. Key Learning Points
        7. Action Items for Follow-up

        Use professional, supportive language that encourages growth and learning.
        """

    def generate_report(self, conversation_history: List[Dict],
                       session_id: str) -> str:
        """
        Generate comprehensive training session report

        Args:
            conversation_history: Complete conversation history
            session_id: Unique session identifier

        Returns:
            str: Formatted training report
        """
        if len(conversation_history) < 2:
            return "Insufficient conversation data for report generation."

        # Analyze the conversation
        analysis = self._analyze_conversation(conversation_history)

        # Get relevant training benchmarks
        training_benchmarks = self._get_training_benchmarks(conversation_history)

        # Generate comprehensive report
        messages = [
            {
                "role": "user",
                "content": f"""
                Generate a comprehensive training report for this hotel guest service interaction:

                SESSION ID: {session_id}
                DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

                CONVERSATION ANALYSIS:
                {analysis}

                RELEVANT TRAINING BENCHMARKS:
                {training_benchmarks}

                FULL CONVERSATION:
                {self._format_detailed_conversation(conversation_history)}

                Create a professional training report that includes:
                1. Executive Summary (2-3 sentences)
                2. Scenario Overview (what type of guest issue, complexity level)
                3. Performance Highlights (specific examples of good service)
                4. Development Opportunities (specific areas needing improvement)
                5. Training Recommendations (based on training materials)
                6. Key Learning Points (main takeaways)
                7. Follow-up Actions (specific next steps)

                Format as markdown for easy reading.
                """
            }
        ]

        report = self._make_llm_request(messages, self.get_system_prompt())

        if self.validate_response(report):
            # Save report for record keeping
            self._save_report(session_id, report, conversation_history)
            return report
        else:
            return self._generate_basic_report(conversation_history, session_id)

    def generate_summary_metrics(self, conversation_history: List[Dict]) -> Dict[str, Any]:
        """
        Generate quantitative metrics for the session

        Args:
            conversation_history: Complete conversation history

        Returns:
            Dict: Performance metrics and scores
        """
        if len(conversation_history) < 2:
            return {"error": "Insufficient data"}

        context = self._format_conversation_history(conversation_history)

        messages = [
            {
                "role": "user",
                "content": f"""
                Analyze this guest service interaction and provide quantitative assessment:

                {context}

                Rate performance in these areas (1-5 scale where 5 is excellent):
                - Initial response appropriateness
                - Empathy and active listening
                - Problem-solving effectiveness
                - Communication clarity
                - Professional demeanor
                - Service recovery techniques
                - Overall guest satisfaction achieved

                Also provide:
                - Conversation length (number of exchanges)
                - Issue resolution status (resolved/partially resolved/unresolved)
                - Guest sentiment progression (improved/neutral/deteriorated)
                - Training objectives met (list)

                Respond in valid JSON format only.
                """
            }
        ]

        response = self._make_llm_request(
            messages,
            "You are a customer service analytics expert. Provide accurate numerical assessments in JSON format."
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Return basic metrics if parsing fails
            return {
                "conversation_length": len(conversation_history),
                "timestamp": datetime.now().isoformat(),
                "analysis_error": "Could not parse detailed metrics"
            }

    def _analyze_conversation(self, conversation_history: List[Dict]) -> str:
        """
        Perform detailed conversation analysis

        Args:
            conversation_history: Complete conversation history

        Returns:
            str: Detailed analysis
        """
        context = self._format_conversation_history(conversation_history)

        messages = [
            {
                "role": "user",
                "content": f"""
                Analyze this guest service conversation in detail:

                {context}

                Provide analysis of:
                1. Guest issue type and complexity
                2. Agent response patterns and techniques used
                3. Conversation flow and resolution progression
                4. Key decision points and outcomes
                5. Adherence to service standards

                Provide a comprehensive analysis (3-4 paragraphs).
                """
            }
        ]

        analysis = self._make_llm_request(
            messages,
            "You are a customer service expert analyzing training interactions."
        )

        return analysis if analysis else "Analysis could not be completed."

    def _get_training_benchmarks(self, conversation_history: List[Dict]) -> str:
        """
        Retrieve relevant training benchmarks and standards

        Args:
            conversation_history: Conversation to analyze

        Returns:
            str: Relevant training content
        """
        # Identify the issue type for targeted retrieval
        query = self._extract_issue_keywords(conversation_history)

        # Get relevant training materials
        relevant_docs = self.rag_retriever.retrieve_relevant_content(
            f"{query} training standards best practices", top_k=5
        )

        if relevant_docs:
            return "\n".join([f"- {doc['content']}" for doc in relevant_docs])
        else:
            return "No specific training benchmarks retrieved for this scenario type."

    def _extract_issue_keywords(self, conversation_history: List[Dict]) -> str:
        """
        Extract keywords related to the guest issue

        Args:
            conversation_history: Conversation history

        Returns:
            str: Key terms for retrieval
        """
        # Get first guest message (usually contains the main issue)
        for msg in conversation_history:
            if msg["role"] == "guest":
                return msg["content"][:200]  # First 200 chars should capture the issue

        return "guest service interaction"

    def _format_detailed_conversation(self, conversation_history: List[Dict]) -> str:
        """
        Format conversation with timestamps and role clarity

        Args:
            conversation_history: Complete conversation

        Returns:
            str: Formatted conversation
        """
        formatted_lines = []

        for i, msg in enumerate(conversation_history):
            role_name = "🏨 Hotel Guest" if msg["role"] == "guest" else "👨‍💼 Front Desk Agent"
            timestamp = msg.get("timestamp", datetime.now()).strftime("%H:%M:%S")

            formatted_lines.append(f"[{timestamp}] {role_name}: {msg['content']}")

        return "\n\n".join(formatted_lines)

    def _generate_basic_report(self, conversation_history: List[Dict], session_id: str) -> str:
        """
        Generate basic report if full report generation fails

        Args:
            conversation_history: Conversation history
            session_id: Session identifier

        Returns:
            str: Basic report
        """
        return f"""
# Training Session Report

**Session ID:** {session_id}
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Duration:** {len(conversation_history)} exchanges

## Summary
This training session involved a guest service interaction with {len(conversation_history)} message exchanges.

## Conversation Overview
- **Messages exchanged:** {len(conversation_history)}
- **Session type:** Guest service training simulation

## Next Steps
- Review conversation details with training supervisor
- Identify specific learning objectives for follow-up training
- Practice scenarios similar to this interaction

---
*Report generated automatically by Hotel Training System*
"""

    def _save_report(self, session_id: str, report: str, conversation_history: List[Dict]) -> None:
        """
        Save report to logs for record keeping

        Args:
            session_id: Session identifier
            report: Generated report
            conversation_history: Full conversation
        """
        try:
            report_data = {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "report": report,
                "conversation_length": len(conversation_history),
                "generated_by": "ReportAgent"
            }

            # This could be saved to database or file system
            self.logger.info(f"Report generated for session {session_id}")

        except Exception as e:
            self.logger.error(f"Failed to save report for session {session_id}: {e}")