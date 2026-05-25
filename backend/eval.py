from rag import ask_rag

TESTS = [
    {
        "question": "Where is payment handled?",
        "expected_source": "payment.ts"
    },
    {
        "question": "Which file renders checkout?",
        "expected_source": "Checkout.tsx"
    },
    {
        "question": "Where is the reusable button component?",
        "expected_source": "Button.tsx"
    }
]


def run_eval():
    passed = 0

    for test in TESTS:
        result = ask_rag(test["question"])
        sources = result.get("sources", [])

        matched = any(
            test["expected_source"] in source
            for source in sources
        )

        status = "PASS" if matched else "FAIL"

        print(f"{status}: {test['question']}")
        print(f"Expected source: {test['expected_source']}")
        print(f"Actual sources: {sources}")
        print("---")

        if matched:
            passed += 1

    print(f"Score: {passed}/{len(TESTS)}")


if __name__ == "__main__":
    run_eval()