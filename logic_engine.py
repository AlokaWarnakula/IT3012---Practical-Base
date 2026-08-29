# logic_engine.py
"""Practical 5 - Knowledge Base + Forward Chaining Inference Engine.

Up to Lab 4 the agent only asked "can I physically walk there?" (walls, bounds).
That is REACHABILITY. This module gives the agent a way to also ask "can I prove
it is safe to walk there?" - FEASIBILITY - by storing knowledge DECLARATIVELY
(facts + Horn clause rules) instead of as nested if-else statements in the agent.
"""


class KnowledgeBase:
    """Part 1, Step 1.1 - a tiny propositional KB.

    facts : set  -> unique string propositions currently believed true
                    (the percepts, plus everything inferred from them)
    rules : list -> Horn clauses stored as tuples (premise_list, conclusion)
                    e.g. (['TargetVisible', 'HasDust'], 'SafeToEngage')
                    read as: TargetVisible AND HasDust => SafeToEngage
    """

    def __init__(self):
        self.facts = set()     # To store unique string facts
        self.rules = []        # To store rules as Tuples: (premises, conclusion)

    # ---- Telling the KB what we know ------------------------------------
    def tell_fact(self, fact_string):
        """Assert a percept/proposition as TRUE."""
        self.facts.add(fact_string)

    def tell_rule(self, premise_list, conclusion_string):
        """Assert a Horn clause: (p1 AND p2 AND ...) => conclusion."""
        self.rules.append((premise_list, conclusion_string))

    def clear_facts(self):
        """Wipe the percepts but KEEP the rules.

        Rules are permanent domain knowledge; facts are per-tile sensor data,
        so A* clears them before reasoning about each new neighbour.
        """
        self.facts.clear()

    # ---- Part 2, Step 2.1: the inference engine -------------------------
    def forward_chain(self):
        """Data-driven forward chaining (repeated Modus Ponens).

        Keep sweeping the whole rule list until one full pass deduces nothing
        new - that fixed point is when the KB is saturated, and it is what lets
        a conclusion from one rule (SafeToEngage) fire a later rule (Retreat).
        """
        new_facts_added = True

        while new_facts_added:
            new_facts_added = False

            for premises, conclusion in self.rules:
                if conclusion not in self.facts:
                    # Modus Ponens check: are ALL premises already believed?
                    if all(p in self.facts for p in premises):
                        self.facts.add(conclusion)     # ... therefore conclusion
                        new_facts_added = True
