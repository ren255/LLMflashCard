"""File model for file management."""

from sqlalchemy import Column, Integer, Text, TIMESTAMP, text, Index
from sqlalchemy.orm import relationship
from .base import Base


class File(Base):
    """File management table."""
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(Text, nullable=False)
    original_name = Column(Text)
    file_path = Column(Text, nullable=False)
    collection = Column(Text)
    file_type = Column(Text)  # image, flashcard, text, etc.
    file_size = Column(Integer)
    hash = Column(Text, unique=True)
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    # Relationships
    image = relationship("Image", back_populates="file",
                         uselist=False, cascade="all, delete-orphan")
    flashcard = relationship(
        "Flashcard", back_populates="file", uselist=False, cascade="all, delete-orphan")
    llm_files = relationship(
        "LLMFile", back_populates="file", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_files_hash', 'hash'),
        Index('idx_files_file_type', 'file_type'),
        Index('idx_files_collection', 'collection'),
    )

    def __repr__(self):
        return f"<File(id={self.id}, filename='{self.filename}', file_type='{self.file_type}')>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_name': self.original_name,
            'file_path': self.file_path,
            'collection': self.collection,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'hash': self.hash,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
