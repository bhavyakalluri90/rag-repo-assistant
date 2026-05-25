from rag import ask_rag

TESTS = [
    {
        "question": "Where is routing handled?",
        "expected_source": "routes",
    },
    {
        "question": "Where is Redux configured?",
        "expected_source": "store",
    },
    {
        "question": "Where are product pages implemented?",
        "expected_source": "Product",
    },
]


def run_eval():
    passed = 0

    for test in TESTS:
        result = ask_rag(test["question"], mode="files")
        sources = result.get("sources", [])

        matched = any(
            test["expected_source"].lower() in source.lower()
            for source in sources
        )

        print("PASS" if matched else "FAIL", "-", test["question"])
        print("Expected:", test["expected_source"])
        print("Sources:", sources)
        print("---")

        if matched:
            passed += 1

    print(f"Score: {passed}/{len(TESTS)}")


if __name__ == "__main__":
    run_eval()