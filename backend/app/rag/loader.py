from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class TranscriptDocument:
    """A parsed Lenny's Podcast transcript."""

    guest: str
    title: str
    episode_url: str | None
    publish_date: str | None
    content: str
    source_path: str


class TranscriptLoader:
    """Loads transcript.md files from the Lenny transcript repository."""

    def __init__(self, transcripts_root: str | Path):
        self.transcripts_root = Path(transcripts_root)

    def find_transcripts(self) -> list[Path]:
        """Find every transcript.md file in the corpus."""

        if not self.transcripts_root.exists():
            raise FileNotFoundError(
                f"Transcript directory does not exist: "
                f"{self.transcripts_root}"
            )

        return sorted(
            self.transcripts_root.rglob("transcript.md")
        )

    def load_file(self, path: Path) -> TranscriptDocument:
        """Parse one transcript.md file."""

        raw_text = path.read_text(
            encoding="utf-8"
        )

        metadata, transcript = self._parse_frontmatter(
            raw_text
        )

        content = self._clean_transcript(transcript)

        if not content:
            raise ValueError(
                f"Transcript is empty: {path}"
            )

        return TranscriptDocument(
            guest=str(metadata.get("guest", "")),
            title=str(metadata.get("title", "")),
            episode_url=metadata.get("youtube_url"),
            publish_date=(
                str(metadata["publish_date"])
                if metadata.get("publish_date")
                else None
            ),
            content=content,
            source_path=str(path),
        )

    def load_all(self) -> list[TranscriptDocument]:
        """Load every transcript in the corpus."""

        documents = []

        for path in self.find_transcripts():
            try:
                documents.append(
                    self.load_file(path)
                )
            except (ValueError, yaml.YAMLError) as exc:
                print(
                    f"Skipping {path}: {exc}"
                )

        return documents

    @staticmethod
    def _parse_frontmatter(
        raw_text: str,
    ) -> tuple[dict, str]:
        """Separate YAML frontmatter from transcript content."""

        text = raw_text.lstrip()

        if not text.startswith("---"):
            return {}, text

        parts = text.split("---", 2)

        if len(parts) != 3:
            raise ValueError(
                "Invalid YAML frontmatter"
            )

        frontmatter_text = parts[1].strip()
        transcript_text = parts[2].strip()

        metadata = yaml.safe_load(
            frontmatter_text
        ) or {}

        if not isinstance(metadata, dict):
            raise ValueError(
                "Transcript metadata must be a YAML object"
            )

        return metadata, transcript_text

    @staticmethod
    def _clean_transcript(
        transcript: str,
    ) -> str:
        """Remove markdown-only structure while preserving dialogue."""

        lines = []

        for line in transcript.splitlines():
            stripped = line.strip()

            if not stripped:
                continue

            if stripped.startswith("## Transcript"):
                continue

            if stripped.startswith("# "):
                continue

            lines.append(stripped)

        return "\n".join(lines)