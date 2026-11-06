import hashlib
import logging
import warnings
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from bson import BSON
from gridfs import GridFSBucket
from pypdf import PdfReader, overwrite_configuration

from backend.app import app
from backend.extensions import mongo

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ("en", "ta", "ml", "kn", "te")
MAX_DOCUMENT_BYTES = 16 * 1024 * 1024

# Supplied PDFs include vector artwork with unusually large compressed streams.
overwrite_configuration(
    stream_decoding_work_maximum_length=500_000_000,
    stream_parsing_work_maximum_count=50_000_000,
    zlib_maximum_output_length=500_000_000,
)

BOOKS = {
    "English BOOK.zip": {
        "subject": "English",
        "titles": {
            "jeff101": "A Letter to God",
            "jeff102": "Nelson Mandela: Long Walk to Freedom",
            "jeff103": "Two Stories about Flying",
            "jeff104": "From the Diary of Anne Frank",
            "jeff105": "Glimpses of India",
            "jeff106": "Mijbil the Otter",
            "jeff107": "Madam Rides the Bus",
            "jeff108": "The Sermon at Benares",
            "jeff109": "The Proposal",
        },
    },
    "Maths Book.zip": {
        "subject": "Mathematics",
        "titles": {
            "jemh101": "Real Numbers",
            "jemh102": "Polynomials",
            "jemh103": "Pair of Linear Equations in Two Variables",
            "jemh104": "Quadratic Equations",
            "jemh105": "Arithmetic Progressions",
            "jemh106": "Triangles",
            "jemh107": "Coordinate Geometry",
            "jemh108": "Introduction to Trigonometry",
            "jemh109": "Some Applications of Trigonometry",
            "jemh110": "Circles",
            "jemh111": "Areas Related to Circles",
            "jemh112": "Surface Areas and Volumes",
            "jemh113": "Statistics",
            "jemh114": "Probability",
        },
    },
    "Science book.zip": {
        "subject": "Science",
        "titles": {
            "jesc101": "Chemical Reactions and Equations",
            "jesc102": "Acids, Bases and Salts",
            "jesc103": "Metals and Non-metals",
            "jesc104": "Carbon and its Compounds",
            "jesc105": "Life Processes",
            "jesc106": "Control and Coordination",
            "jesc107": "How do Organisms Reproduce?",
            "jesc108": "Heredity",
            "jesc109": "Light: Reflection and Refraction",
            "jesc110": "The Human Eye and the Colourful World",
            "jesc111": "Electricity",
            "jesc112": "Magnetic Effects of Electric Current",
            "jesc113": "Our Environment",
        },
    },
    "SOCIAL BOOK.zip": {
        "subject": "Social Science",
        "titles": {
            "jess401": "Power-sharing",
            "jess402": "Federalism",
            "jess403": "Gender, Religion and Caste",
            "jess404": "Political Parties",
            "jess405": "Outcomes of Democracy",
        },
    },
}


def _source_kind(stem: str, titles: dict[str, str]) -> str:
    if stem in titles:
        return "chapter"
    if stem.endswith("ps"):
        return "front_matter"
    if stem.endswith("an"):
        return "answer_key"
    if stem.endswith("a1") or stem.endswith("a2"):
        return "appendix"
    raise ValueError(f"Unclassified textbook PDF: {stem}")


def _extract_source(archive_name: str, filename: str, pdf_bytes: bytes, subject: str, kind: str) -> dict:
    reader = PdfReader(BytesIO(pdf_bytes))
    if reader.is_encrypted and not reader.decrypt(""):
        raise ValueError(f"Encrypted PDF cannot be imported: {archive_name}/{filename}")

    page_text = [page.extract_text() or "" for page in reader.pages]
    extracted_text = "\n\n".join(
        f"[Page {page_number}]\n{text.strip()}"
        for page_number, text in enumerate(page_text, start=1)
        if text.strip()
    )
    if not extracted_text:
        raise ValueError(f"No extractable text found in {archive_name}/{filename}")

    stem = Path(filename).stem.lower()
    source_id = f"cbse10_{stem}"
    title = BOOKS[archive_name]["titles"].get(stem, Path(filename).stem)
    document = {
        "source_id": source_id,
        "source_archive": archive_name,
        "source_file": filename,
        "subject": subject,
        "title": title,
        "kind": kind,
        "language": "en",
        "page_count": len(reader.pages),
        "text": extracted_text,
        "sha256": hashlib.sha256(pdf_bytes).hexdigest(),
        "imported_at": datetime.now(timezone.utc),
    }
    if len(BSON.encode(document)) >= MAX_DOCUMENT_BYTES:
        raise ValueError(f"Extracted PDF exceeds MongoDB's document limit: {archive_name}/{filename}")
    return document


def _curriculum_document(source: dict) -> dict:
    stem = Path(source["source_file"]).stem.lower()
    chapter_number = int(stem[-2:])
    subject_slug = source["subject"].lower().replace(" ", "_")
    title = BOOKS[source["source_archive"]]["titles"][stem]
    return {
        "concept_id": f"cbse10_textbook_{subject_slug}_{stem}",
        "source_id": source["source_id"],
        "source_kind": "cbse_textbook",
        "source_archive": source["source_archive"],
        "grade": "10",
        "board": "CBSE",
        "subject": source["subject"],
        "chapter": f"Chapter {chapter_number}",
        "chapter_number": chapter_number,
        "lesson": title,
        "title": {"en": title},
        "keywords": [],
        "quiz": [],
        "review_status": "approved",
        "translation_status": {language: "source_text" if language == "en" else "TODO_REVIEW" for language in LANGUAGES},
    }


def import_textbooks() -> None:
    warnings.filterwarnings("ignore", module="pypdf")
    logging.getLogger("pypdf").setLevel(logging.ERROR)

    sources = []
    curriculum = []
    replacements = 0
    with app.app_context():
        archive_entries = {}
        for archive_name, book in BOOKS.items():
            archive_path = ROOT / archive_name
            if not archive_path.is_file():
                raise FileNotFoundError(f"Required textbook archive not found: {archive_path}")
            with ZipFile(archive_path) as archive:
                for filename in archive.namelist():
                    if not filename.lower().endswith(".pdf"):
                        continue
                    archive_entries[(archive_name, filename)] = archive_path
                    stem = Path(filename).stem.lower()
                    kind = _source_kind(stem, book["titles"])
                    source = _extract_source(
                        archive_name,
                        filename,
                        archive.read(filename),
                        book["subject"],
                        kind,
                    )
                    replacements += source["text"].count("\ufffd")
                    sources.append(source)
                    if kind == "chapter":
                        curriculum.append(_curriculum_document(source))

        if len(sources) != 49 or len(curriculum) != 41:
            raise RuntimeError(f"Unexpected textbook inventory: {len(sources)} PDFs, {len(curriculum)} chapters")

        mongo.cx.admin.command("ping")
        mongo.db.textbook_sources.create_index("source_id", unique=True)
        mongo.db.curriculum.create_index("source_id", unique=True, sparse=True)

        bucket = GridFSBucket(mongo.db)
        for source in sources:
            archive_path = archive_entries[(source["source_archive"], source["source_file"])]
            with ZipFile(archive_path) as archive:
                pdf_bytes = archive.read(source["source_file"])
            if hashlib.sha256(pdf_bytes).hexdigest() != source["sha256"]:
                raise RuntimeError(f"Textbook PDF changed during import: {source['source_file']}")

            existing = mongo.db["fs.files"].find_one({
                "filename": source["source_id"],
                "metadata.source_id": source["source_id"],
            })
            if existing and existing.get("metadata", {}).get("sha256") != source["sha256"]:
                bucket.delete(existing["_id"])
                existing = None
            if existing is None:
                source["gridfs_file_id"] = bucket.upload_from_stream(
                    source["source_id"],
                    BytesIO(pdf_bytes),
                    metadata={
                        "source_id": source["source_id"],
                        "source_file": source["source_file"],
                        "sha256": source["sha256"],
                    },
                )
            else:
                source["gridfs_file_id"] = existing["_id"]
            mongo.db.textbook_sources.update_one(
                {"source_id": source["source_id"]},
                {"$set": source},
                upsert=True,
            )
        for concept in curriculum:
            mongo.db.curriculum.update_one(
                {"concept_id": concept["concept_id"]},
                {"$set": concept},
                upsert=True,
            )

        print(
            f"Imported {len(sources)} PDFs and {len(curriculum)} chapter lessons "
            f"into {mongo.db.name}; source PDFs are stored in GridFS; "
            f"extracted replacement characters: {replacements}."
        )


if __name__ == "__main__":
    import_textbooks()
