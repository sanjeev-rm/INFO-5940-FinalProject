"""
Guest Agent

Simulates hotel guest interactions for training purposes.
Creates realistic scenarios and responds to front desk agent interactions.
"""

import random
from typing import List, Dict, Any
from .base_agent import BaseAgent

class GuestAgent(BaseAgent):
    """AI agent that simulates hotel guest interactions"""

    def __init__(self, config):
        super().__init__(config, model_preference="balanced")
        self.scenario_types = [
            "room_issue",
            "billing_dispute",
            "service_complaint",
            "amenity_problem",
            "booking_issue",
            "noise_complaint",
            "lost_item",
            "late_checkout"
        ]

    def get_system_prompt(self) -> str:
        """Get system prompt for guest agent"""
        return """
        You are playing the role of a hotel guest who has encountered an issue and needs assistance from the front desk.
        Your goal is to create a realistic training scenario for front desk staff.

        IMPORTANT GUIDELINES:
        - Start with a clear problem or concern
        - Show appropriate emotions (frustrated, disappointed, concerned, etc.)
        - Be realistic but not abusive or inappropriate
        - Give the agent opportunities to demonstrate good service recovery
        - Respond to the agent's attempts to help
        - If the agent provides good service, gradually become more satisfied
        - If the agent provides poor service, become more frustrated (but remain civil)

        PERSONALITY TRAITS TO EXHIBIT:
        - Be human and realistic
        - Show emotions appropriate to the situation
        - Be willing to be satisfied if the agent handles things well
        - Provide clear feedback about what's working or not working

        Keep responses conversational and realistic. Vary your communication style.
        """

    def generate_scenario(self) -> str:
        """Generate initial guest scenario"""
        scenario_type = random.choice(self.scenario_types)

        scenarios = {
            "room_issue": [
                "Excuse me, I just checked into room 314 and the air conditioning isn't working. It's really hot in there and I can't sleep like this.",
                "Hi, I'm in room 207 and the TV remote isn't working. Also, one of the lamps won't turn on. Can you help me with this?",
                "I need help with my room - room 156. The shower has no hot water and I have an important meeting in an hour."
            ],
            "billing_dispute": [
                "I'm checking out and there are charges on my bill that I don't understand. What is this $25 'resort fee' that wasn't mentioned when I booked?",
                "Excuse me, my bill shows room service charges but I never ordered room service. Can you explain this?",
                "I'm looking at my bill and I'm being charged for movies I didn't watch. This needs to be fixed before I check out."
            ],
            "service_complaint": [
                "I'm really disappointed with the housekeeping service. I put out the 'clean room' sign yesterday morning and my room was never cleaned.",
                "The restaurant staff was incredibly rude to me at dinner last night. I'd like to speak with a manager about this.",
                "I've been waiting 30 minutes for the valet to bring my car. This is completely unacceptable for a hotel of this caliber."
            ],
            "amenity_problem": [
                "The pool was supposed to be open until 10 PM according to your website, but it's closed now at 8:30. My kids are really disappointed.",
                "The fitness center equipment is broken and there's no sign saying when it will be fixed. I specifically chose this hotel for the gym.",
                "I can't connect to the WiFi and I have important work to do. The password you gave me isn't working."
            ],
            "booking_issue": [
                "I booked a king bed room but you've given me a room with two double beds. I specifically need a king bed.",
                "My reservation shows I'm supposed to have a room with a balcony and ocean view, but this room faces the parking lot.",
                "I made this reservation three months ago for a non-smoking room, but this room clearly smells like smoke."
            ],
            "noise_complaint": [
                "The room next to mine has been extremely loud all night. There's shouting and music and I haven't been able to sleep at all.",
                "There's construction noise starting at 6 AM right outside my window. Nobody told me about this when I checked in.",
                "The people upstairs are being incredibly loud - it sounds like they're moving furniture around at midnight."
            ],
            "lost_item": [
                "I think I left my phone charger in the conference room yesterday. Has anyone turned one in? It's a white iPhone charger.",
                "I can't find my car keys anywhere. I'm wondering if housekeeping might have seen them when they cleaned my room?",
                "My daughter left her stuffed animal in the restaurant at lunch. It's pink and really important to her - has anyone found it?"
            ],
            "late_checkout": [
                "My flight got delayed and now I won't be leaving until 3 PM. Is it possible to get a late checkout? I know it's last minute.",
                "I have a family emergency and need to extend my stay another night. Do you have availability in the same room?",
                "I'm willing to pay for a late checkout - my meeting ran long and I need a few more hours to pack and prepare."
            ]
        }

        return random.choice(scenarios[scenario_type])

    def respond_to_agent(self, conversation_history: List[Dict], agent_response: str) -> str:
        """
        Generate guest response based on agent's response

        Args:
            conversation_history: Previous conversation
            agent_response: Latest agent response

        Returns:
            str: Guest's response
        """
        # Format conversation for context
        context = self._format_conversation_history(conversation_history)

        # Create prompt for response generation
        messages = [
            {
                "role": "user",
                "content": f"""
                Based on this conversation:
                {context}

                The front desk agent just said: "{agent_response}"

                How should the hotel guest respond? Consider:
                - Is the agent being helpful and professional?
                - Is the agent offering appropriate solutions?
                - How satisfied should the guest be with this response?
                - What would be a realistic next step in this conversation?

                Generate a realistic guest response that continues the training scenario appropriately.
                """
            }
        ]

        response = self._make_llm_request(messages, self.get_system_prompt())

        # Validate and return response
        if self.validate_response(response):
            return response
        else:
            return "I appreciate your help with this issue. What can we do to resolve it?"

    def escalate_scenario(self, conversation_history: List[Dict]) -> str:
        """
        Escalate the scenario if the agent isn't handling it well

        Args:
            conversation_history: Previous conversation

        Returns:
            str: Escalated guest response
        """
        context = self._format_conversation_history(conversation_history)

        messages = [
            {
                "role": "user",
                "content": f"""
                Based on this conversation:
                {context}

                The guest's issue doesn't seem to be getting resolved effectively.
                Generate a response where the guest becomes more concerned but remains professional.
                The guest should express urgency or ask for a manager if appropriate.
                """
            }
        ]

        response = self._make_llm_request(messages, self.get_system_prompt())

        if self.validate_response(response):
            return response
        else:
            return "I'm getting frustrated that this isn't being resolved. Can I speak with your manager please?"