from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


class IntentClassifier:
    _training_data = {
        "lookup": [
            "Where is the policy on remote work?",
            "Which document contains the compliance section?",
            "Show me the onboarding guidance in the handbook.",
            "Where is the vendor approval process described?",
        ],
        "summary": [
            "Summarize the security guidelines.",
            "Give me a short summary of the training manual.",
            "What are the key takeaways from the annual report?",
            "Provide a brief overview of the policy changes.",
        ],
        "comparison": [
            "Compare the old and new onboarding process.",
            "What is the difference between policy A and policy B?",
            "How does the compliance guideline differ from the security playbook?",
            "Contrast the two document sets for remote work.",
        ],
        "facts": [
            "What is the deadline for submitting expense claims?",
            "Which department owns the data privacy process?",
            "What is the required approval chain for purchases?",
            "Which policy mandates background checks?",
        ],
        "abstain": [
            "Tell me about my favorite song.",
            "Can you give me a recipe for pancakes?",
            "What is the capital of Jupiter?",
            "Write a poem about the ocean.",
        ],
    }

    def __init__(self):
        labels: list[str] = []
        texts: list[str] = []
        for label, examples in self._training_data.items():
            for example in examples:
                labels.append(label)
                texts.append(example)

        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        self.model = LogisticRegression(max_iter=2000, random_state=42)
        self.model.fit(self.vectorizer.fit_transform(texts), labels)

    def predict(self, question: str) -> str:
        transformed = self.vectorizer.transform([question])
        return self.model.predict(transformed)[0]

    def predict_proba(self, question: str) -> dict[str, float]:
        probas = self.model.predict_proba(self.vectorizer.transform([question]))[0]
        labels = self.model.classes_
        return {label: float(score) for label, score in zip(labels, probas)}
