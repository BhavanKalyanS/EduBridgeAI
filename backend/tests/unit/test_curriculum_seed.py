from scripts.seed_curriculum import CONCEPTS, build_concept


def test_cbse_class_ten_seed_covers_all_core_subjects() -> None:
    subjects = {item["subject"] for item in CONCEPTS}

    assert subjects == {"English", "Hindi", "Mathematics", "Science", "Social Science"}
    assert len(CONCEPTS) >= 20
    assert all(build_concept(item)["grade"] == "10" for item in CONCEPTS)
    assert all(build_concept(item)["board"] == "CBSE" for item in CONCEPTS)


def test_seeded_lessons_have_five_stages_and_valid_localized_answers() -> None:
    for item in CONCEPTS:
        concept = build_concept(item)
        assert set(concept["content"]["ta"]) == {"s0", "s1", "s2", "s3", "s4"}
        assert {question["kind"] for question in concept["quiz"]} == {"concept", "keyword"}
        for question in concept["quiz"]:
            for language in ("ta", "en"):
                assert question["answer"][language] in question["options"][language]
