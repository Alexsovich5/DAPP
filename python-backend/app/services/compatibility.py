# import re
from typing import Any, Dict, List

from app.observability import metrics as obs


class CompatibilityCalculator:
    """
    Local compatibility algorithms for Soul Before Skin matching.
    All processing done locally without external API dependencies.
    Target processing time: <500ms
    """

    def __init__(self):
        self.weights = {
            "interests": 0.25,
            "values": 0.30,
            "demographics": 0.20,
            "communication": 0.15,
            "personality": 0.10,
        }

        # Enhanced value keywords for semantic matching
        self.value_keywords = {
            "relationship_values": {
                "commitment": [
                    "loyal",
                    "faithful",
                    "dedicated",
                    "devoted",
                    "committed",
                    "stable",
                    "monogamous",
                    "exclusive",
                    "forever",
                    "lasting",
                    "permanent",
                    "serious",
                    "long-term",
                    "partnership",
                    "fidelity",
                    "trust",
                    "dependable",
                ],
                "growth": [
                    "learn",
                    "improve",
                    "develop",
                    "evolve",
                    "grow",
                    "better",
                    "progress",
                    "expand",
                    "challenge",
                    "potential",
                    "self-improvement",
                    "education",
                    "wisdom",
                    "knowledge",
                    "enlightenment",
                    "transform",
                ],
                "adventure": [
                    "explore",
                    "travel",
                    "new",
                    "experience",
                    "adventure",
                    "exciting",
                    "spontaneous",
                    "discovery",
                    "journey",
                    "wanderlust",
                    "curiosity",
                    "freedom",
                    "thrill",
                    "explore",
                    "unknown",
                    "risk",
                    "bold",
                ],
                "stability": [
                    "secure",
                    "steady",
                    "reliable",
                    "consistent",
                    "stable",
                    "safe",
                    "predictable",
                    "routine",
                    "comfort",
                    "security",
                    "grounded",
                    "balanced",
                    "foundation",
                    "solid",
                    "dependable",
                    "constant",
                ],
                "independence": [
                    "free",
                    "independent",
                    "space",
                    "individual",
                    "autonomous",
                    "self-reliant",
                    "personal",
                    "freedom",
                    "solo",
                    "own",
                    "myself",
                    "boundaries",
                    "separate",
                    "unique",
                    "distinct",
                    "self-sufficient",
                ],
                "family": [
                    "family",
                    "children",
                    "kids",
                    "marriage",
                    "home",
                    "domestic",
                    "parenthood",
                    "legacy",
                    "generations",
                    "traditions",
                    "roots",
                    "togetherness",
                    "children",
                    "babies",
                    "wedding",
                    "household",
                ],
                "spirituality": [
                    "spiritual",
                    "faith",
                    "belief",
                    "soul",
                    "divine",
                    "meaning",
                    "purpose",
                    "meditation",
                    "prayer",
                    "religion",
                    "transcendent",
                    "connection",
                    "universe",
                    "higher",
                    "sacred",
                    "mindful",
                ],
                "creativity": [
                    "creative",
                    "artistic",
                    "imagination",
                    "innovation",
                    "inspiration",
                    "expression",
                    "beauty",
                    "art",
                    "music",
                    "writing",
                    "design",
                    "original",
                    "unique",
                    "vision",
                    "talent",
                    "passion",
                ],
                "success": [
                    "achievement",
                    "success",
                    "goals",
                    "ambition",
                    "career",
                    "excellence",
                    "accomplishment",
                    "recognition",
                    "leadership",
                    "impact",
                    "influence",
                    "prosperity",
                    "winning",
                    "mastery",
                    "expertise",
                    "professional",
                ],
                "authenticity": [
                    "authentic",
                    "genuine",
                    "real",
                    "honest",
                    "true",
                    "sincere",
                    "transparent",
                    "vulnerable",
                    "open",
                    "truthful",
                    "integrity",
                    "raw",
                    "unfiltered",
                    "natural",
                    "myself",
                    "original",
                ],
            },
            "connection_style": {
                "deep_talks": [
                    "meaningful",
                    "deep",
                    "philosophy",
                    "soul",
                    "profound",
                    "spiritual",
                    "intellectual",
                    "thoughtful",
                    "wisdom",
                    "insights",
                    "consciousness",
                    "existential",
                    "purpose",
                    "values",
                    "beliefs",
                    "truth",
                    "understanding",
                ],
                "shared_activities": [
                    "together",
                    "activities",
                    "hobbies",
                    "fun",
                    "shared",
                    "do",
                    "adventures",
                    "experiences",
                    "explore",
                    "play",
                    "games",
                    "sports",
                    "outdoor",
                    "projects",
                    "cooking",
                    "create",
                    "build",
                    "collaborate",
                ],
                "quality_time": [
                    "present",
                    "attention",
                    "focus",
                    "listen",
                    "time",
                    "together",
                    "undivided",
                    "mindful",
                    "connection",
                    "moment",
                    "here",
                    "now",
                    "exclusive",
                    "dedicated",
                    "uninterrupted",
                    "intimate",
                    "focused",
                ],
                "physical_affection": [
                    "touch",
                    "affection",
                    "close",
                    "intimate",
                    "physical",
                    "hug",
                    "cuddle",
                    "kiss",
                    "hold",
                    "embrace",
                    "caress",
                    "tender",
                    "warmth",
                    "comfort",
                    "skin",
                    "contact",
                    "gentle",
                    "loving",
                ],
                "emotional_support": [
                    "support",
                    "comfort",
                    "encourage",
                    "understand",
                    "empathy",
                    "compassion",
                    "care",
                    "nurture",
                    "help",
                    "listen",
                    "validate",
                    "acceptance",
                    "patience",
                    "kindness",
                    "reassurance",
                    "healing",
                ],
                "playful_connection": [
                    "playful",
                    "humor",
                    "laugh",
                    "joy",
                    "fun",
                    "silly",
                    "spontaneous",
                    "lighthearted",
                    "jokes",
                    "tease",
                    "banter",
                    "witty",
                    "amusing",
                    "cheerful",
                    "entertainment",
                    "comedy",
                    "smile",
                    "giggle",
                ],
            },
            "ideal_evening": {
                "romantic": [
                    "romantic",
                    "candles",
                    "wine",
                    "dinner",
                    "sunset",
                    "stargazing",
                    "intimate",
                    "cozy",
                    "fireplace",
                    "music",
                    "dancing",
                    "champagne",
                    "flowers",
                    "soft",
                    "gentle",
                    "magical",
                    "dreamy",
                    "enchanting",
                ],
                "adventurous": [
                    "adventure",
                    "explore",
                    "new",
                    "exciting",
                    "spontaneous",
                    "travel",
                    "discover",
                    "unknown",
                    "journey",
                    "quest",
                    "bold",
                    "daring",
                    "thrilling",
                    "unexpected",
                    "wild",
                    "freedom",
                    "experience",
                ],
                "peaceful": [
                    "peaceful",
                    "quiet",
                    "calm",
                    "serene",
                    "tranquil",
                    "relaxing",
                    "meditation",
                    "nature",
                    "stillness",
                    "harmony",
                    "balance",
                    "mindful",
                    "zen",
                    "gentle",
                    "soothing",
                    "restful",
                    "comfortable",
                ],
                "social": [
                    "friends",
                    "social",
                    "party",
                    "gathering",
                    "people",
                    "community",
                    "celebration",
                    "group",
                    "lively",
                    "energetic",
                    "vibrant",
                    "connection",
                    "networking",
                    "mingling",
                    "festive",
                    "collective",
                ],
                "creative": [
                    "creative",
                    "art",
                    "music",
                    "writing",
                    "painting",
                    "craft",
                    "imagination",
                    "expression",
                    "inspiration",
                    "beauty",
                    "design",
                    "poetry",
                    "dance",
                    "theater",
                    "innovative",
                    "artistic",
                    "vision",
                ],
            },
            "feeling_understood": {
                "verbal_communication": [
                    "talk",
                    "conversation",
                    "words",
                    "express",
                    "share",
                    "communicate",
                    "discuss",
                    "dialogue",
                    "voice",
                    "speak",
                    "articulate",
                    "explain",
                    "describe",
                    "tell",
                    "story",
                    "language",
                    "verbal",
                    "say",
                ],
                "non_verbal_understanding": [
                    "eyes",
                    "look",
                    "silence",
                    "presence",
                    "energy",
                    "vibe",
                    "feeling",
                    "intuition",
                    "sense",
                    "without",
                    "words",
                    "unspoken",
                    "gesture",
                    "body",
                    "language",
                    "subtle",
                    "implicit",
                    "knowing",
                    "connection",
                ],
                "emotional_validation": [
                    "validate",
                    "accept",
                    "understand",
                    "empathy",
                    "compassion",
                    "feelings",
                    "emotions",
                    "heart",
                    "soul",
                    "support",
                    "comfort",
                    "acknowledgment",
                    "recognition",
                    "respect",
                    "honor",
                    "value",
                ],
                "shared_experiences": [
                    "together",
                    "shared",
                    "experience",
                    "memory",
                    "moment",
                    "common",
                    "mutual",
                    "collective",
                    "bond",
                    "connection",
                    "unity",
                    "harmony",
                    "synchronicity",
                    "parallel",
                    "similar",
                    "relate",
                    "resonate",
                ],
            },
        }

    def calculate_interest_similarity(
        self, user1_interests: List[str], user2_interests: List[str]
    ) -> float:
        """
        Calculate Jaccard similarity coefficient for interests overlap.
        Returns: 0.0 to 1.0 (higher = more similar)
        """
        if not user1_interests or not user2_interests:
            return 0.0

        # Convert to lowercase sets for case-insensitive comparison
        set1 = set([interest.lower().strip() for interest in user1_interests])
        set2 = set([interest.lower().strip() for interest in user2_interests])

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        if union == 0:
            return 0.0

        return intersection / union

    def calculate_values_compatibility(
        self, user1_responses: Dict, user2_responses: Dict
    ) -> float:
        """
        Compare responses to core values questions using keyword matching.
        Returns: 0.0 to 1.0 based on shared values alignment
        """
        if not user1_responses or not user2_responses:
            return 0.0

        compatibility_scores = []

        for question_key in user1_responses.keys():
            if question_key in user2_responses:
                score = self._compare_response_values(
                    user1_responses[question_key],
                    user2_responses[question_key],
                    self.value_keywords.get(question_key, {}),
                )
                compatibility_scores.append(score)

        return (
            sum(compatibility_scores) / len(compatibility_scores)
            if compatibility_scores
            else 0.0
        )

    def _compare_response_values(
        self, response1: str, response2: str, keywords: Dict
    ) -> float:
        """
        Compare two text responses using keyword matching.
        Returns: 0.0 to 1.0 based on shared value indicators
        """
        if not response1 or not response2:
            return 0.0

        # Convert to lowercase for comparison
        resp1_lower = response1.lower()
        resp2_lower = response2.lower()

        # Find matching value categories
        user1_values = set()
        user2_values = set()

        for value_category, keyword_list in keywords.items():
            for keyword in keyword_list:
                if keyword in resp1_lower:
                    user1_values.add(value_category)
                if keyword in resp2_lower:
                    user2_values.add(value_category)

        # Calculate overlap
        if not user1_values and not user2_values:
            return 0.5  # Neutral if no keywords found

        intersection = len(user1_values.intersection(user2_values))
        union = len(user1_values.union(user2_values))

        return intersection / union if union > 0 else 0.0

    def calculate_age_compatibility(self, age1: int, age2: int) -> float:
        """
        Age compatibility with bell curve - optimal within 5 years.
        Returns: 0.0 to 1.0 based on age difference
        """
        age_diff = abs(age1 - age2)

        if age_diff == 0:
            return 1.0
        elif age_diff <= 2:
            return 0.9
        elif age_diff <= 5:
            return 0.8
        elif age_diff <= 8:
            return 0.6
        elif age_diff <= 12:
            return 0.4
        else:
            return 0.2

    def calculate_location_compatibility(self, location1: str, location2: str) -> float:
        """
        Simple location compatibility based on string matching.
        For MVP, basic city/state matching. Can be enhanced with geocoding.
        Returns: 0.0 to 1.0 based on location similarity
        """
        if not location1 or not location2:
            return 0.5  # Neutral if location not provided

        loc1_lower = location1.lower().strip()
        loc2_lower = location2.lower().strip()

        # Exact match
        if loc1_lower == loc2_lower:
            return 1.0

        # City match (assuming format: "City, State")
        city1 = loc1_lower.split(",")[0].strip()
        city2 = loc2_lower.split(",")[0].strip()

        if city1 == city2:
            return 0.9

        # State match
        if "," in loc1_lower and "," in loc2_lower:
            state1 = loc1_lower.split(",")[-1].strip()
            state2 = loc2_lower.split(",")[-1].strip()
            if state1 == state2:
                return 0.6

        return 0.3  # Different locations but willing to consider

    def calculate_demographic_compatibility(
        self, user1_data: Dict, user2_data: Dict
    ) -> float:
        """
        Calculate compatibility based on age and location.
        Returns: 0.0 to 1.0 based on demographic alignment
        """
        age_score = 0.5  # Default if age not available
        location_score = 0.5  # Default if location not available

        # Calculate age compatibility
        if user1_data.get("age") and user2_data.get("age"):
            age_score = self.calculate_age_compatibility(
                user1_data["age"], user2_data["age"]
            )

        # Calculate location compatibility
        if user1_data.get("location") and user2_data.get("location"):
            location_score = self.calculate_location_compatibility(
                user1_data["location"], user2_data["location"]
            )

        return (age_score * 0.4) + (location_score * 0.6)

    def calculate_communication_compatibility(
        self, user1_data: Dict, user2_data: Dict
    ) -> float:
        """
        Calculate communication style compatibility based on user preferences.
        Returns: 0.0 to 1.0 based on communication style alignment
        """
        comm1 = user1_data.get("communication_style", {})
        comm2 = user2_data.get("communication_style", {})

        if not comm1 or not comm2:
            return 0.6  # Default moderate compatibility if data missing

        compatibility_factors = []

        # Check preferred communication style
        style1 = comm1.get("preferred_style", "").lower()
        style2 = comm2.get("preferred_style", "").lower()

        if style1 and style2:
            if style1 == style2:
                compatibility_factors.append(1.0)
            elif self._are_complementary_styles(style1, style2):
                compatibility_factors.append(0.8)
            else:
                compatibility_factors.append(0.5)

        # Check response time preferences
        response1 = comm1.get("response_preference", "").lower()
        response2 = comm2.get("response_preference", "").lower()

        if response1 and response2:
            if response1 == response2:
                compatibility_factors.append(0.9)
            elif self._are_compatible_response_styles(response1, response2):
                compatibility_factors.append(0.7)
            else:
                compatibility_factors.append(0.4)

        # Check emotional communication style from onboarding responses
        if user1_data.get("emotional_responses") and user2_data.get(
            "emotional_responses"
        ):
            emotional_compat = self._analyze_emotional_communication_style(
                user1_data["emotional_responses"], user2_data["emotional_responses"]
            )
            compatibility_factors.append(emotional_compat)

        return (
            sum(compatibility_factors) / len(compatibility_factors)
            if compatibility_factors
            else 0.6
        )

    def _are_complementary_styles(self, style1: str, style2: str) -> bool:
        """Check if two communication styles are complementary."""
        complementary_pairs = {
            ("deep_conversation", "thoughtful_listening"),
            ("expressive", "supportive"),
            ("direct", "understanding"),
            ("playful", "encouraging"),
        }
        return (style1, style2) in complementary_pairs or (
            style2,
            style1,
        ) in complementary_pairs

    def _are_compatible_response_styles(self, response1: str, response2: str) -> bool:
        """Check if response time preferences are compatible."""
        compatible_responses = {
            ("immediate", "quick"),
            ("thoughtful", "considered"),
            ("flexible", "adaptable"),
        }
        return (response1, response2) in compatible_responses or (
            response2,
            response1,
        ) in compatible_responses

    def _analyze_emotional_communication_style(
        self, responses1: Dict, responses2: Dict
    ) -> float:
        """Analyze emotional communication compatibility from onboarding responses."""
        # Keywords indicating communication styles
        communication_indicators = {
            "expressive": [
                "express",
                "share",
                "open",
                "communicate",
                "talk",
                "discuss",
            ],
            "reflective": ["think", "consider", "reflect", "contemplate", "understand"],
            "supportive": ["support", "listen", "care", "help", "encourage", "comfort"],
            "direct": ["direct", "honest", "straightforward", "clear", "upfront"],
            "gentle": ["gentle", "kind", "patient", "calm", "peaceful", "soft"],
        }

        user1_styles = set()
        user2_styles = set()

        # Analyze all emotional responses for communication style indicators
        for response in responses1.values():
            if isinstance(response, str):
                response_lower = response.lower()
                for style, keywords in communication_indicators.items():
                    if any(keyword in response_lower for keyword in keywords):
                        user1_styles.add(style)

        for response in responses2.values():
            if isinstance(response, str):
                response_lower = response.lower()
                for style, keywords in communication_indicators.items():
                    if any(keyword in response_lower for keyword in keywords):
                        user2_styles.add(style)

        # Calculate overlap and complementarity
        if not user1_styles or not user2_styles:
            return 0.6

        overlap = len(user1_styles.intersection(user2_styles))
        total_styles = len(user1_styles.union(user2_styles))

        # Higher score for some overlap but not identical (diversity is good)
        if overlap == 0:
            return 0.4
        elif overlap == len(user1_styles) == len(user2_styles):
            return 0.8  # Very similar styles
        else:
            return 0.6 + (overlap / total_styles) * 0.3

    def calculate_personality_compatibility(
        self, user1_data: Dict, user2_data: Dict
    ) -> float:
        """
        Calculate personality trait compatibility based on user data.
        Returns: 0.0 to 1.0 based on personality alignment and complementarity
        """
        traits1 = user1_data.get("personality_traits", {})
        traits2 = user2_data.get("personality_traits", {})

        if not traits1 or not traits2:
            # Analyze personality from emotional responses if traits not available
            if user1_data.get("emotional_responses") and user2_data.get(
                "emotional_responses"
            ):
                return self._analyze_personality_from_responses(
                    user1_data["emotional_responses"], user2_data["emotional_responses"]
                )
            return 0.6  # Default if no personality data

        compatibility_scores = []

        # Big Five personality traits analysis (if available)
        big_five_traits = [
            "openness",
            "conscientiousness",
            "extraversion",
            "agreeableness",
            "neuroticism",
        ]

        for trait in big_five_traits:
            score1 = traits1.get(trait, 50)  # Default middle score
            score2 = traits2.get(trait, 50)

            # Some traits work better with similarity, others with complementarity
            if trait in ["agreeableness", "conscientiousness"]:
                # These traits benefit from similarity
                trait_compat = 1.0 - abs(score1 - score2) / 100.0
            elif trait == "neuroticism":
                # Lower neuroticism scores are generally better, balance is key
                avg_neuroticism = (score1 + score2) / 2
                trait_compat = max(0.3, 1.0 - avg_neuroticism / 100.0)
            else:
                # Openness and extraversion can be complementary
                # Perfect similarity gets 0.9, moderate difference gets 0.8, extreme difference gets 0.4
                diff = abs(score1 - score2)
                if diff <= 20:
                    trait_compat = 0.9
                elif diff <= 40:
                    trait_compat = 0.8
                elif diff <= 60:
                    trait_compat = 0.6
                else:
                    trait_compat = 0.4

            compatibility_scores.append(trait_compat)

        return (
            sum(compatibility_scores) / len(compatibility_scores)
            if compatibility_scores
            else 0.6
        )

    def _analyze_personality_from_responses(
        self, responses1: Dict, responses2: Dict
    ) -> float:
        """Extract personality indicators from emotional onboarding responses."""
        personality_indicators = {
            "openness": [
                "new",
                "experience",
                "creative",
                "curious",
                "explore",
                "learn",
                "adventure",
            ],
            "conscientiousness": [
                "organized",
                "responsible",
                "plan",
                "goal",
                "dedicated",
                "reliable",
            ],
            "extraversion": [
                "people",
                "social",
                "outgoing",
                "energy",
                "talk",
                "connect",
                "friends",
            ],
            "agreeableness": [
                "help",
                "kind",
                "compassionate",
                "understanding",
                "empathy",
                "care",
            ],
            "emotional_stability": [
                "calm",
                "stable",
                "confident",
                "peaceful",
                "balanced",
                "strong",
            ],
        }

        user1_traits = {}
        user2_traits = {}

        # Analyze responses for personality indicators
        for trait, keywords in personality_indicators.items():
            count1 = 0
            count2 = 0

            for response in responses1.values():
                if isinstance(response, str):
                    response_lower = response.lower()
                    count1 += sum(
                        1 for keyword in keywords if keyword in response_lower
                    )

            for response in responses2.values():
                if isinstance(response, str):
                    response_lower = response.lower()
                    count2 += sum(
                        1 for keyword in keywords if keyword in response_lower
                    )

            # Normalize scores (0-100 scale)
            user1_traits[trait] = min(100, count1 * 20)
            user2_traits[trait] = min(100, count2 * 20)

        # Calculate compatibility using similar logic as above
        compatibility_scores = []
        for trait in personality_indicators.keys():
            score1 = user1_traits.get(trait, 30)
            score2 = user2_traits.get(trait, 30)

            if trait in ["agreeableness", "conscientiousness"]:
                trait_compat = 1.0 - abs(score1 - score2) / 100.0
            elif trait == "emotional_stability":
                # Higher emotional stability is generally better
                avg_stability = (score1 + score2) / 2
                trait_compat = min(1.0, avg_stability / 80.0)
            else:
                diff = abs(score1 - score2)
                if diff <= 20:
                    trait_compat = 0.9
                elif diff <= 40:
                    trait_compat = 0.7
                else:
                    trait_compat = 0.5

            compatibility_scores.append(trait_compat)

        return (
            sum(compatibility_scores) / len(compatibility_scores)
            if compatibility_scores
            else 0.6
        )

    def calculate_overall_compatibility(
        self, user1_data: Dict, user2_data: Dict
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive compatibility score between two users.

        Args:
            user1_data: Dict containing user1's profile data
            user2_data: Dict containing user2's profile data

        Returns:
            Dict with total compatibility, breakdown, and match quality
        """
        with obs.compatibility_calc_seconds.time():
            # Calculate individual scores
            interest_score = self.calculate_interest_similarity(
                user1_data.get("interests", []), user2_data.get("interests", [])
            )

            values_score = self.calculate_values_compatibility(
                user1_data.get("core_values", {}),
                user2_data.get("core_values", {}),
            )

            demographic_score = self.calculate_demographic_compatibility(
                user1_data, user2_data
            )

            # Calculate communication and personality compatibility using new methods
            communication_score = self.calculate_communication_compatibility(
                user1_data, user2_data
            )
            personality_score = self.calculate_personality_compatibility(
                user1_data, user2_data
            )

            # Calculate weighted total
            total_score = (
                interest_score * self.weights["interests"]
                + values_score * self.weights["values"]
                + demographic_score * self.weights["demographics"]
                + communication_score * self.weights["communication"]
                + personality_score * self.weights["personality"]
            )

            return {
                "total_compatibility": round(total_score * 100, 1),
                "breakdown": {
                    "interests": round(interest_score * 100, 1),
                    "values": round(values_score * 100, 1),
                    "demographics": round(demographic_score * 100, 1),
                    "communication": round(communication_score * 100, 1),
                    "personality": round(personality_score * 100, 1),
                },
                "match_quality": self._get_match_quality_label(total_score),
                "explanation": self._generate_compatibility_explanation(
                    total_score, interest_score, values_score, demographic_score
                ),
            }

    def _get_match_quality_label(self, score: float) -> str:
        """Convert compatibility score to descriptive label."""
        if score >= 0.8:
            return "Exceptional Soul Connection"
        elif score >= 0.7:
            return "Strong Compatibility"
        elif score >= 0.6:
            return "Good Potential"
        elif score >= 0.5:
            return "Moderate Match"
        else:
            return "Explore Further"

    def _generate_compatibility_explanation(
        self,
        total: float,
        interests: float,
        values: float,
        demographics: float,
    ) -> str:
        """Generate human-readable explanation of compatibility."""
        explanations = []

        if interests >= 0.7:
            explanations.append("shared interests create natural conversation topics")
        elif interests >= 0.4:
            explanations.append("some common interests provide connection points")

        if values >= 0.7:
            explanations.append(
                "strong alignment in core values and relationship goals"
            )
        elif values >= 0.4:
            explanations.append("compatible values foundation for deeper connection")

        if demographics >= 0.7:
            explanations.append("well-matched in lifestyle and location preferences")

        if not explanations:
            explanations.append("potential for discovering unexpected connections")

        return "This match shows " + " and ".join(explanations) + "."


def get_compatibility_calculator() -> CompatibilityCalculator:
    """Factory function to create compatibility calculator instance."""
    return CompatibilityCalculator()
