"""Flashcard model for flashcard-specific information."""

from sqlalchemy import Column, Integer, Text, ForeignKey, text
from sqlalchemy.orm import relationship
from .base import Base

class Flashcard(Base):
    """Flashcard-specific information table."""
    __tablename__ = 'flashcards'
    
    file_id = Column(Integer, ForeignKey('files.id', ondelete='CASCADE'), primary_key=True)
    encoding = Column(Text, server_default='utf-8')
    
    # Relationships
    file = relationship("File", back_populates="flashcard")
    
    def __repr__(self):
        return f"<Flashcard(file_id={self.file_id}, encoding='{self.encoding}')>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'file_id': self.file_id,
            'encoding': self.encoding
        }
    
    def read_content(self):
        """Read flashcard content from file."""
        if self.file and self.file.file_path:
            try:
                with open(self.file.file_path, 'r', encoding=self.encoding) as f:
                    return f.read()
            except FileNotFoundError:
                return None
            except UnicodeDecodeError:
                # Try with different encoding if specified encoding fails
                try:
                    with open(self.file.file_path, 'r', encoding='utf-8') as f:
                        return f.read()
                except:
                    return None
        return None