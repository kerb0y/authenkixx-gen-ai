"""Compare 2 intent-classification models on the same dummy data.

Metric: accuracy and macro F1 on the same held-out test split
(stratified, test_size=0.25, random_state=42). Also runs a small
hyperparameter search for LogisticRegression (C in [0.1, 1, 10],
3-fold CV on the training split only) and reports its effect.

Run from gen-ai/:  python scripts/train_compare.py
Output: prints a comparison table and writes outputs/model_comparison.json
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

from app.classifier import load_training_data

OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "outputs",
    "model_comparison.json",
)


def evaluate(model, X_test, y_test):
    pred = model.predict(X_test)
    return {
        "accuracy": round(float(accuracy_score(y_test, pred)), 4),
        "macro_f1": round(float(f1_score(y_test, pred, average="macro")), 4),
    }


def main():
    texts, labels = load_training_data()
    counts = dict(collections.Counter(labels))
    print("Class counts (dummy data):", counts)
    print("Total dummy labelled examples:", len(texts))
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.25, random_state=42, stratify=labels
    )
    print(f"Train: {len(X_train)}  Test: {len(X_test)} (stratified, seed 42)")

    lr = Pipeline(
        [
            ("tfidf", TfidfVectorizer()),
            (
                "clf",
                LogisticRegression(max_iter=1000, class_weight="balanced", C=1.0),
            ),
        ]
    )
    nb = Pipeline(
        [("tfidf", TfidfVectorizer()), ("clf", MultinomialNB())]
    )
    lr.fit(X_train, y_train)
    nb.fit(X_train, y_train)
    lr_metrics = evaluate(lr, X_test, y_test)
    nb_metrics = evaluate(nb, X_test, y_test)

    grid = GridSearchCV(
        Pipeline(
            [
                ("tfidf", TfidfVectorizer()),
                (
                    "clf",
                    LogisticRegression(max_iter=1000, class_weight="balanced"),
                ),
            ]
        ),
        param_grid={"clf__C": [0.1, 1.0, 10.0]},
        cv=3,
        scoring="f1_macro",
    )
    grid.fit(X_train, y_train)
    tuned_metrics = evaluate(grid.best_estimator_, X_test, y_test)

    result = {
        "data": "dummy labelled data only (gen-ai/data/dummy_intents.csv)",
        "split": "stratified test_size=0.25 random_state=42",
        "class_counts": counts,
        "train_size": len(X_train),
        "test_size": len(X_test),
        "models": {
            "logistic_regression_C1": lr_metrics,
            "multinomial_nb": nb_metrics,
            "logistic_regression_tuned": {
                **tuned_metrics,
                "best_C": grid.best_params_["clf__C"],
                "best_cv_macro_f1": round(float(grid.best_score_), 4),
            },
        },
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"Saved to {OUT}")


if __name__ == "__main__":
    main()
