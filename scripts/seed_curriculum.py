from backend.app import app
from backend.extensions import mongo

LANGUAGES = ("en", "ta", "ml", "kn", "te")
EMPTY_STAGES = {f"s{stage}": "" for stage in range(5)}

CONCEPTS = [
    {
        "concept_id": "math9_alg_variable", "title_en": "Variables", "title_ta": "மாறிகள்",
        "ta": "ஒரு மாறி என்பது மாறக்கூடிய மதிப்பைக் குறிக்கும் எழுத்து. ஒரே எழுத்து வரும் இடங்களில் அதே மதிப்பைப் பயன்படுத்த வேண்டும்.",
        "en": "A variable is a letter that represents a value that can change. The same letter stands for the same value wherever it appears.",
        "example_ta": "எடுத்துக்காட்டு: x + 5 = 12 என்றால், x என்பது அறியப்படாத எண்ணைக் குறிக்கிறது.", "example_en": "Example: In x + 5 = 12, x represents the unknown number.",
        "question_ta": "x + 5 = 12 எனில், x-ன் மதிப்பு என்ன?", "question_en": "If x + 5 = 12, what is x?", "options_ta": ["7", "17", "5"], "options_en": ["7", "17", "5"], "answer": "7", "term": "variable", "distractors": ["constant", "coefficient"],
    },
    {
        "concept_id": "math9_alg_expression", "title_en": "Algebraic expressions", "title_ta": "இயற்கணிதக் கோவைகள்",
        "ta": "எண்கள், மாறிகள், செயல்குறிகள் இணைந்த அமைப்பு இயற்கணிதக் கோவை. சமக்குறி இல்லாததால் அது சமன்பாடு அல்ல.",
        "en": "An algebraic expression combines numbers, variables and operations. It has no equals sign, so it is not an equation.",
        "example_ta": "எடுத்துக்காட்டு: 3x + 2 என்பது ஒரு கோவை.", "example_en": "Example: 3x + 2 is an expression.",
        "question_ta": "இவற்றில் இயற்கணிதக் கோவை எது?", "question_en": "Which of these is an algebraic expression?", "options_ta": ["3x + 2", "3x = 2", "x > 2"], "options_en": ["3x + 2", "3x = 2", "x > 2"], "answer": "3x + 2", "term": "expression", "distractors": ["equation", "inequality"],
    },
    {
        "concept_id": "math9_alg_like_terms", "title_en": "Like terms", "title_ta": "ஒத்த உறுப்புகள்",
        "ta": "ஒரே மாறிகளும் ஒரே அடுக்குகளும் உள்ள உறுப்புகள் ஒத்த உறுப்புகள். அவற்றின் குணகங்களை மட்டும் கூட்டலாம் அல்லது கழிக்கலாம்.",
        "en": "Like terms have the same variables raised to the same powers. Their coefficients can be added or subtracted.",
        "example_ta": "எடுத்துக்காட்டு: 3x மற்றும் 5x ஒத்த உறுப்புகள்; 3x + 5x = 8x.", "example_en": "Example: 3x and 5x are like terms; 3x + 5x = 8x.",
        "question_ta": "எந்த ஜோடி ஒத்த உறுப்புகள்?", "question_en": "Which pair contains like terms?", "options_ta": ["3x, 5x", "3x, 5y", "x, x²"], "options_en": ["3x, 5x", "3x, 5y", "x, x²"], "answer": "3x, 5x", "term": "like terms", "distractors": ["unlike terms", "exponents"],
    },
    {
        "concept_id": "math9_alg_simplify", "title_en": "Simplifying expressions", "title_ta": "கோவைகளை எளிமைப்படுத்துதல்",
        "ta": "ஒரு கோவையில் ஒத்த உறுப்புகளைச் சேர்த்து அதன் எளிய வடிவத்தைப் பெறலாம். மாறிகளின் அடுக்குகளை மாற்ற வேண்டாம்.",
        "en": "Combine like terms in an expression to write it in a simpler form. Do not change the powers of the variables.",
        "example_ta": "எடுத்துக்காட்டு: 2x + 4 + 3x = 5x + 4.", "example_en": "Example: 2x + 4 + 3x = 5x + 4.",
        "question_ta": "2x + 4 + 3x-ன் எளிய வடிவம் எது?", "question_en": "What is the simplified form of 2x + 4 + 3x?", "options_ta": ["5x + 4", "5x + 7", "6x + 4"], "options_en": ["5x + 4", "5x + 7", "6x + 4"], "answer": "5x + 4", "term": "simplify", "distractors": ["expand", "evaluate"],
    },
    {
        "concept_id": "math9_alg_equation", "title_en": "Linear equations", "title_ta": "நேரியல் சமன்பாடுகள்",
        "ta": "சமக்குறி கொண்ட கூற்று சமன்பாடு. சமன்பாட்டின் இருபுறமும் ஒரே செயலைச் செய்தால் சமநிலை நிலைக்கும்.",
        "en": "An equation is a statement with an equals sign. Doing the same operation on both sides preserves equality.",
        "example_ta": "எடுத்துக்காட்டு: x + 4 = 10 என்பது ஒரு நேரியல் சமன்பாடு.", "example_en": "Example: x + 4 = 10 is a linear equation.",
        "question_ta": "எந்த கூற்று சமன்பாடு?", "question_en": "Which statement is an equation?", "options_ta": ["x + 4 = 10", "x + 4", "x > 4"], "options_en": ["x + 4 = 10", "x + 4", "x > 4"], "answer": "x + 4 = 10", "term": "equation", "distractors": ["expression", "inequality"],
    },
    {
        "concept_id": "math9_alg_solve", "title_en": "Solving equations", "title_ta": "சமன்பாடுகளைத் தீர்த்தல்",
        "ta": "மாறியைத் தனியாக்கி சமன்பாட்டை உண்மையாக்கும் மதிப்பைக் காண்க. ஒவ்வொரு படியிலும் இருபுறமும் சமமாகச் செயற்படுங்கள்.",
        "en": "Isolate the variable to find a value that makes the equation true. Keep both sides balanced at every step.",
        "example_ta": "எடுத்துக்காட்டு: x + 4 = 10 எனில், இருபுறத்திலிருந்தும் 4-ஐக் கழித்து x = 6.", "example_en": "Example: For x + 4 = 10, subtract 4 from both sides to get x = 6.",
        "question_ta": "2x = 14 எனில், x எவ்வளவு?", "question_en": "If 2x = 14, what is x?", "options_ta": ["7", "12", "16"], "options_en": ["7", "12", "16"], "answer": "7", "term": "solve", "distractors": ["substitute", "simplify"],
    },
    {
        "concept_id": "math9_alg_distributive", "title_en": "Distributive property", "title_ta": "பரவல் பண்பு",
        "ta": "அடைப்புக்குறிக்கு வெளியே உள்ள எண்ணை உள்ளே உள்ள ஒவ்வொரு உறுப்புடனும் பெருக்குவது பரவல் பண்பு.",
        "en": "The distributive property multiplies the factor outside parentheses by every term inside them.",
        "example_ta": "எடுத்துக்காட்டு: 3(x + 2) = 3x + 6.", "example_en": "Example: 3(x + 2) = 3x + 6.",
        "question_ta": "2(x + 5)-ன் விரிவு எது?", "question_en": "What is the expansion of 2(x + 5)?", "options_ta": ["2x + 10", "2x + 5", "x + 10"], "options_en": ["2x + 10", "2x + 5", "x + 10"], "answer": "2x + 10", "term": "distribute", "distractors": ["factor", "combine"],
    },
    {
        "concept_id": "math9_coord_pairs", "title_en": "Coordinate pairs", "title_ta": "ஆயத்தொலைவு ஜோடிகள்",
        "ta": "ஒரு புள்ளியின் இடத்தை (x, y) என்ற வரிசைப்படுத்தப்பட்ட ஜோடி குறிக்கும். முதலில் கிடைமட்ட x மதிப்பு, அடுத்து செங்குத்து y மதிப்பு.",
        "en": "An ordered pair (x, y) locates a point. The horizontal x-value comes first, followed by the vertical y-value.",
        "example_ta": "எடுத்துக்காட்டு: (3, 2) என்பது வலப்புறம் 3, மேலே 2 நகரும் புள்ளி.", "example_en": "Example: (3, 2) is 3 units right and 2 units up from the origin.",
        "question_ta": "(4, 1)-இல் x-ன் மதிப்பு எது?", "question_en": "In (4, 1), what is the x-coordinate?", "options_ta": ["4", "1", "5"], "options_en": ["4", "1", "5"], "answer": "4", "term": "coordinate", "distractors": ["origin", "axis"],
    },
]


def build_concept(item: dict) -> dict:
    title = {"en": item["title_en"], "ta": item["title_ta"], "ml": "", "kn": "", "te": ""}
    content = {"ta": {
        "s0": f"{item['ta']}\n\n{item['example_ta']}",
        "s1": f"{item['ta']}\n\n{item['example_ta']}\n\nKey English term: {item['term']}.",
        "s2": f"{item['ta']}\n\n{item['en']}\n\n{item['example_ta']}",
        "s3": f"{item['en']}\n\nதமிழ் உதவி: {item['ta']}\n\n{item['example_en']}",
        "s4": f"{item['en']}\n\n{item['example_en']}",
    }, "en": {
        "s0": f"{item['ta']}\n\n{item['example_ta']}",
        "s1": f"{item['ta']}\n\n{item['example_ta']}\n\nKey English term: {item['term']}.",
        "s2": f"{item['ta']}\n\n{item['en']}\n\n{item['example_en']}",
        "s3": f"{item['en']}\n\nRegional-language support: {item['ta']}\n\n{item['example_en']}",
        "s4": f"{item['en']}\n\n{item['example_en']}",
    }}
    for language in ("ml", "kn", "te"):
        content[language] = dict(EMPTY_STAGES)

    quiz = []
    questions = [
        ("concept", item["question_ta"], item["question_en"], item["options_ta"], item["options_en"], item["answer"]),
        ("keyword", f"{item['title_ta']} என்ற கருத்திற்கான English term எது?", "Which English term matches this concept?", [item["term"], *item["distractors"]], [item["term"], *item["distractors"]], item["term"]),
    ]
    for index, (kind, question_ta, question_en, options_ta, options_en, answer) in enumerate(questions, start=1):
        quiz.append({
            "q_id": f"{item['concept_id']}_q{index}",
            "kind": kind,
            "question": {"ta": question_ta, "en": question_en},
            "options": {"ta": options_ta, "en": options_en},
            "answer": {"ta": answer, "en": answer},
        })

    return {
        "concept_id": item["concept_id"],
        "subject": "Mathematics",
        "grade": "9",
        "chapter": "Algebra and coordinates",
        "lesson": item["title_en"],
        "title": title,
        "keywords": [{"en": item["term"], "ta": item["title_ta"], "ml": "", "kn": "", "te": ""}],
        "content": content,
        "quiz": quiz,
        "review_status": "approved",
        "translation_status": {"en": "reviewed", "ta": "reviewed", "ml": "TODO_REVIEW", "kn": "TODO_REVIEW", "te": "TODO_REVIEW"},
    }


def seed_curriculum() -> None:
    with app.app_context():
        for item in CONCEPTS:
            document = build_concept(item)
            mongo.db.curriculum.update_one({"concept_id": document["concept_id"]}, {"$set": document}, upsert=True)
        print(f"Seeded {len(CONCEPTS)} synthetic Grade 9 Mathematics concepts.")


if __name__ == "__main__":
    seed_curriculum()