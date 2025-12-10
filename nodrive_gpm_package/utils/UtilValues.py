import os, difflib, re
from mutagen import File


def getFilePathOnFolderStore(dirStore: str, nameFile: str) -> str:
    for file in os.listdir(dirStore):
        if file.startswith(nameFile + "."):
            return os.path.join(dirStore, file)
    return ""


def calculateSimilarity(text1: str, text2: str) -> float:

    def normalizeText(text: str) -> str:
        """Normalize text by removing extra whitespace, newlines, and special chars"""
        if not text:
            return ""

        # Remove extra whitespace and newlines
        normalized = re.sub(r"\s+", " ", text.strip())

        # Remove common invisible characters
        normalized = normalized.replace("\r", "").replace("\n", " ").replace("\t", " ")

        # Remove multiple spaces
        normalized = re.sub(r" +", " ", normalized)

        return normalized.strip()

    """Calculate similarity percentage between two texts"""
    if not text1 and not text2:
        return 100.0

    if not text1 or not text2:
        return 0.0

    # Normalize texts first
    norm1 = normalizeText(text1)
    norm2 = normalizeText(text2)

    # Use SequenceMatcher to calculate similarity
    similarity = difflib.SequenceMatcher(None, norm1, norm2).ratio()

    return similarity * 100
