"""LLM output models for managing LLM interactions."""

import json
from sqlalchemy import Column, Integer, Text, TIMESTAMP, ForeignKey, text, PrimaryKeyConstraint, Index
from sqlalchemy.orm import relationship
from .base import Base


class LLMOutput(Base):
    """LLM output management table."""
    __tablename__ = 'LLM_outputs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    files_num = Column(Integer)  # Number of related files in LLM_files
    prompt = Column(Text)        # Prompt content
    output = Column(Text)        # LLM output
    model_name = Column(Text)    # Model used
    params = Column(Text)        # JSON format parameters
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    # Relationships
    llm_files = relationship(
        "LLMFile", back_populates="llm_output", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_LLM_outputs_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<LLMOutput(id={self.id}, model_name='{self.model_name}', files_num={self.files_num})>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'files_num': self.files_num,
            'prompt': self.prompt,
            'output': self.output,
            'model_name': self.model_name,
            'params': self.get_params_dict(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def get_params_dict(self):
        """Get parameters as dictionary."""
        if self.params:
            try:
                return json.loads(self.params)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_params_dict(self, params_dict):
        """Set parameters from dictionary."""
        if params_dict:
            self.params = json.dumps(params_dict)
        else:
            self.params = None

    @property
    def files(self):
        """Get associated files."""
        return [llm_file.file for llm_file in self.llm_files]


class LLMFile(Base):
    """LLM output and file association table (many-to-many)."""
    __tablename__ = 'LLM_files'

    LLM_output_id = Column(Integer, ForeignKey(
        'LLM_outputs.id', ondelete='CASCADE'))
    file_id = Column(Integer, ForeignKey('files.id', ondelete='CASCADE'))

    __table_args__ = (
        PrimaryKeyConstraint('LLM_output_id', 'file_id'),
        Index('idx_LLM_files_file_id', 'file_id'),
    )
    
    # Relationships
    llm_output = relationship("LLMOutput", back_populates="llm_files")
    file = relationship("File", back_populates="llm_files")

    def __repr__(self):
        return f"<LLMFile(LLM_output_id={self.LLM_output_id}, file_id={self.file_id})>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'LLM_output_id': self.LLM_output_id,
            'file_id': self.file_id
        }
