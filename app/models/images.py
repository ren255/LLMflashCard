"""Image model for image-specific information."""

from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Image(Base):
    """Image-specific information table."""
    __tablename__ = 'images'
    
    file_id = Column(Integer, ForeignKey('files.id', ondelete='CASCADE'), primary_key=True)
    image_type = Column(Text)
    region_index = Column(Integer)
    parent_image_id = Column(Integer)
    mask_image_id = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    format = Column(Text)
    thumbnail_path = Column(Text)
    
    # Relationships
    file = relationship("File", back_populates="image")
    
    def __repr__(self):
        return f"<Image(file_id={self.file_id}, image_type='{self.image_type}', width={self.width}, height={self.height})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'file_id': self.file_id,
            'image_type': self.image_type,
            'region_index': self.region_index,
            'parent_image_id': self.parent_image_id,
            'mask_image_id': self.mask_image_id,
            'width': self.width,
            'height': self.height,
            'format': self.format,
            'thumbnail_path': self.thumbnail_path
        }
    
    @property
    def dimensions(self):
        """Return image dimensions as tuple."""
        return (self.width, self.height) if self.width and self.height else None
    
    @property
    def aspect_ratio(self):
        """Calculate aspect ratio."""
        if self.width and self.height and self.height != 0:
            return self.width / self.height
        return None