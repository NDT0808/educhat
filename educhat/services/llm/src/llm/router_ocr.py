from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from common.auth import verify_jwt, TokenData
from common.logging import setup_logger

logger = setup_logger("router_ocr")
router = APIRouter()

def get_ocr_service(request: Request):
    return request.app.state.ocr_service

@router.post("/scan")
async def scan_image(
    file: UploadFile = File(...),
    current_user: TokenData = Depends(verify_jwt),
    ocr_service = Depends(get_ocr_service)
):
    """
    Endpoint nhận ảnh tải lên và trả về kết quả nhận diện chữ (Google Lens style).
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File tải lên phải là hình ảnh (jpg, png...)")
        
    try:
        # Đọc dữ liệu bytes từ file ảnh
        image_bytes = await file.read()
        
        # Đưa vào OCR Service xử lý
        results = await ocr_service.scan_image(image_bytes)
        
        return {
            "status": "success",
            "message": "Quét ảnh thành công",
            "data": results
        }
    except Exception as e:
        logger.error(f"Lỗi khi quét ảnh OCR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
