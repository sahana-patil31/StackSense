from enum import Enum


class QueryType(str, Enum):
    CODE = "CODE"
    DEPENDENCY = "DEPENDENCY"
    DEPLOYMENT = "DEPLOYMENT"
    INCIDENT = "INCIDENT"
    RISK = "RISK"
    GENERAL = "GENERAL"


class QueryRouter:
    terms = {QueryType.CODE: ("code", "function", "class", "file", "repository"), QueryType.DEPENDENCY: ("depend", "import", "calls", "relationship"), QueryType.DEPLOYMENT: ("deploy", "release", "production", "environment"), QueryType.INCIDENT: ("incident", "error", "failure", "outage", "anomaly"), QueryType.RISK: ("risk", "probability", "critical", "score"), QueryType.GENERAL: ()}

    def classify(self, question: str) -> QueryType:
        lowered = question.lower()
        scores = {kind: sum(term in lowered for term in terms) for kind, terms in self.terms.items()}
        return max((kind for kind in scores if scores[kind]), key=lambda kind: scores[kind], default=QueryType.GENERAL)

    def strategies(self, question: str) -> list[QueryType]:
        primary = self.classify(question)
        return [primary] + ([QueryType.CODE, QueryType.DEPENDENCY] if primary in (QueryType.CODE, QueryType.DEPENDENCY) else [])
