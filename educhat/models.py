from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class ContentNode(BaseModel):
    url: str
    type: str = Field(..., description="Type of content: 'page', 'pdf', 'image'")
    content: str = Field(..., description="Text content or image description")
    children: List['ContentNode'] = Field(default_factory=list, description="Nested content (sub-pages, attachments)")
    metadata: Dict = Field(default_factory=dict, description="Extra info like title, size, depth")
    
    # OCR-related fields
    ocr_confidence: Optional[float] = Field(None, description="OCR quality score")
    image_path: Optional[str] = Field(None, description="Local path to downloaded image")

    class Config:
        # Allow recursive self-reference
        populate_by_name = True

class ImageContent(BaseModel):
    """Represents an image and its OCR result"""
    url: str
    local_path: Optional[str] = None
    ocr_text: str = ""
    ocr_confidence: Optional[float] = None
    
class UniversityInfo(BaseModel):
    """Structured information about a university"""
    name: str = Field(..., description="University name")
    url: str = Field(..., description="Detail page URL")
    region: str = Field(..., description="Geographic region")
    content: str = Field(default="", description="Extracted text information")
    images: List[ImageContent] = Field(default_factory=list, description="Processed images with OCR")
    tables: List[str] = Field(default_factory=list, description="Extracted table data in markdown format")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")

# Update forward ref for recursive model
ContentNode.model_rebuild()
