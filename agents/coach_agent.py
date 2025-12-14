"""
Coach Agent

Provides real-time coaching feedback to front desk agents based on training materials.
Uses RAG system to retrieve relevant training content and provide specific guidance.
"""

from typing import List, Dict, Any, Optional
from .base_agent import BaseAgent
from rag_system.retriever import RAGRetriever

class CoachAgent(BaseAgent):
    """AI agent that provides coaching feedback based on training materials"""

    def __init__(self, config, rag_retriever: RAGRetriever):
        super().__init__(config, model_preference="smart")
        self.rag_retriever = rag_retriever

    def get_system_prompt(self) -> str:
        """Get system prompt for coach agent"""
        return """
        You are an expert hotel service trainer providing real-time coaching to front desk agents.
        Your role is to help agents improve their customer service skills based on established training materials.

        COACHING PRINCIPLES:
        - Be constructive and supportive, never harsh or critical
        - Provide specific, actionable feedback
        - Reference training materials when relevant
        - Identify both strengths and areas for improvement
        - Suggest specific phrases or approaches when helpful
        - Focus on service recovery techniques
        - Emphasize empathy, professionalism, and problem-solving

        FEEDBACK STRUCTURE:
        - Start with what the agent did well (if anything)
        - Identify specific areas for improvement
        - Provide concrete suggestions or alternatives
        - Reference relevant training principles
        - Keep feedback concise but helpful

        Remember: Your goal is to help the agent learn and improve, not to criticize.
        """

    def provide_coaching(self, conversation_history: List[Dict],
                        agent_response: str) -> str:
        """
        Provide coaching feedback on agent's response

        Args:
            conversation_history: Previous conversation
            agent_response: Agent's latest response

        Returns:
            str: Coaching feedback
        """
        # Get relevant training content
        training_context = self._get_relevant_training_content(
            conversation_history, agent_response
        )

        # Analyze the situation
        situation_analysis = self._analyze_situation(conversation_history)

        # Generate coaching feedback
        messages = [
            {
                "role": "user",
                "content": f"""
                SITUATION: {situation_analysis}

                AGENT RESPONSE TO EVALUATE: "{agent_response}"

                RELEVANT TRAINING CONTENT:
                {training_context}

                CONVERSATION CONTEXT:
                {self._format_conversation_history(conversation_history[-4:])}

                Provide coaching feedback for this front desk agent response. Focus on:
                1. What did the agent do well?
                2. What could be improved?
                3. Specific suggestions based on training materials
                4. Any missed opportunities for better service recovery

                Keep feedback concise but actionable.
                """
            }
        ]

        coaching_response = self._make_llm_request(messages, self.get_system_prompt())

        # Check if training materials adequately covered this situation
        self._identify_training_gaps(situation_analysis, training_context)

        return coaching_response if self.validate_response(coaching_response) else "Keep practicing active listening and empathy."

    def _get_relevant_training_content(self, conversation_history: List[Dict],
                                     agent_response: str) -> str:
        """
        Retrieve relevant training content using RAG system

        Args:
            conversation_history: Previous conversation
            agent_response: Agent's latest response

        Returns:
            str: Relevant training content
        """
        # Extract key topics from the conversation
        query_terms = []

        # Get the latest guest message to understand the issue type
        for msg in reversed(conversation_history):
            if msg["role"] == "guest":
                query_terms.append(msg["content"])
                break

        # Add agent response for context
        query_terms.append(agent_response)

        # Query RAG system for relevant training content
        query = " ".join(query_terms)
        relevant_docs = self.rag_retriever.retrieve_relevant_content(
            query, top_k=3
        )

        if relevant_docs:
            return "\n".join([doc["content"] for doc in relevant_docs])
        else:
            return "No specific training materials found for this situation."

    def _analyze_situation(self, conversation_history: List[Dict]) -> str:
        """
        Analyze the current situation and guest issue type

        Args:
            conversation_history: Previous conversation

        Returns:
            str: Situation analysis
        """
        if not conversation_history:
            return "Initial guest interaction"

        # Get the last few messages to understand context
        recent_context = self._format_conversation_history(conversation_history[-3:])

        messages = [
            {
                "role": "user",
                "content": f"""
                Based on this conversation:
                {recent_context}

                Identify:
                1. What type of guest issue is this? (billing, room problem, service complaint, etc.)
                2. What is the guest's emotional state?
                3. What stage of service recovery are we in?
                4. What are the key challenges the agent needs to address?

                Provide a brief analysis (2-3 sentences).
                """
            }
        ]

        analysis = self._make_llm_request(
            messages,
            "You are an expert in hotel service analysis. Provide clear, concise situation assessments."
        )

        return analysis if analysis else "Guest service interaction in progress"

    def _identify_training_gaps(self, situation: str, training_content: str) -> None:
        """
        Identify gaps in training materials

        Args:
            situation: Current situation analysis
            training_content: Retrieved training content
        """
        if "No specific training materials found" in training_content:
            self.logger.warning(f"Training gap identified: {situation}")

            # Log this for future training material updates
            gap_info = {
                "timestamp": str(self.config.get_current_timestamp()),
                "situation": situation,
                "missing_content": "Specific guidance for this situation"
            }

            # This could be stored in a database or file for review
            self.logger.info(f"Training gap logged: {gap_info}")

    def get_performance_metrics(self, conversation_history: List[Dict]) -> Dict[str, Any]:
        """
        Analyze overall performance metrics for the conversation

        Args:
            conversation_history: Full conversation history

        Returns:
            Dict: Performance metrics
        """
        if len(conversation_history) < 2:
            return {"status": "insufficient_data"}

        context = self._format_conversation_history(conversation_history)

        messages = [
            {
                "role": "user",
                "content": f"""
                Analyze this complete guest service interaction:
                {context}

                Provide performance assessment in these areas:
                - Empathy and active listening (1-5 scale)
                - Problem-solving effectiveness (1-5 scale)
                - Professional communication (1-5 scale)
                - Service recovery techniques (1-5 scale)
                - Overall guest satisfaction likely achieved (1-5 scale)

                Respond in JSON format with numerical scores and brief explanations.
                """
            }
        ]

        response = self._make_llm_request(
            messages,
            "You are a customer service training expert. Provide objective performance assessments."
        )

        try:
            import json
            return json.loads(response)
        except:
            return {"status": "analysis_error", "raw_response": response}