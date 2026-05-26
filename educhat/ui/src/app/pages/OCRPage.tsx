import React, { useState, useRef } from 'react';
import { Camera, Upload, ScanLine, AlertCircle, Sparkles } from 'lucide-react';
import { apiService } from '../services/apiService';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';

export default function OCRPage() {
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      setSelectedImage(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResults([]);
      setError(null); 
    }
  };

  const handleScan = async () => {
    if (!selectedImage) return;
    
    setLoading(true);
    setError(null);
    try {
      const response = await apiService.scanOCRImage(selectedImage);
      if (response && response.data) {
        setResults(response.data);
      } else {
        setError("Không nhận được dữ liệu hợp lệ từ máy chủ.");
      }
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Đã xảy ra lỗi trong quá trình xử lý ảnh. Vui lòng đảm bảo backend đang hoạt động.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full space-y-6 p-6 max-w-5xl mx-auto w-full">
      <div className="flex flex-col space-y-2">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <ScanLine className="h-8 w-8 text-blue-600" />
          Google Lens OCR Scanner
        </h1>
        <p className="text-slate-500 text-lg">
          Tải lên một bức ảnh để hệ thống AI (TrOCR + CRAFT) nhận diện và bóc tách nội dung chữ cái.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 h-full">
        {/* Upload & Preview Column */}
        <Card className="flex flex-col shadow-md border-blue-100">
          <CardHeader>
            <CardTitle className="text-xl">Bức ảnh của bạn</CardTitle>
            <CardDescription>Chọn ảnh từ máy tính để phân tích</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col flex-1 items-center justify-center space-y-4">
            {previewUrl ? (
              <div className="relative w-full rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 overflow-hidden flex items-center justify-center min-h-[300px]">
                <img 
                  src={previewUrl} 
                  alt="Preview" 
                  className="max-w-full max-h-[400px] object-contain relative z-10"
                />
                
                {/* Draw Bounding Boxes if results exist */}
                {results.length > 0 && (
                  <div className="absolute inset-0 z-20 pointer-events-none">
                    {/* Note: In a real app, drawing exact boxes over a scaled img requires precise coordinate mapping.
                        For simplicity, we just show the results in the list pane. */}
                  </div>
                )}
              </div>
            ) : (
              <div 
                className="w-full min-h-[300px] flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer"
                onClick={() => fileInputRef.current?.click()}
              >
                <div className="h-20 w-20 rounded-full bg-blue-100 flex items-center justify-center mb-4">
                  <Camera className="h-10 w-10 text-blue-600" />
                </div>
                <h3 className="text-lg font-semibold text-slate-700">Tải ảnh lên</h3>
                <p className="text-sm text-slate-500 mt-1">Nhấn để chọn file (JPG, PNG)</p>
              </div>
            )}
            
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileChange} 
              accept="image/*" 
              className="hidden" 
            />
            
            <div className="flex gap-4 w-full pt-4">
              <Button 
                variant="outline" 
                className="w-full"
                onClick={() => fileInputRef.current?.click()}
                disabled={loading}
              >
                <Upload className="mr-2 h-4 w-4" /> Chọn ảnh khác
              </Button>
              <Button 
                className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                onClick={handleScan}
                disabled={!selectedImage || loading}
              >
                {loading ? (
                  <><ScanLine className="mr-2 h-4 w-4 animate-spin" /> Đang quét AI...</>
                ) : (
                  <><Sparkles className="mr-2 h-4 w-4" /> Quét Văn Bản</>
                )}
              </Button>
            </div>
            
            {error && (
              <Alert variant="destructive" className="w-full mt-4">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Lỗi</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Results Column */}
        <Card className="flex flex-col shadow-md">
          <CardHeader className="bg-slate-50 border-b">
            <CardTitle className="text-xl">Kết quả Nhận diện</CardTitle>
            <CardDescription>
              {results.length > 0 
                ? `Tìm thấy ${results.length} khối văn bản.` 
                : "Chưa có dữ liệu."}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex-1 overflow-auto p-0">
            {loading ? (
              <div className="flex flex-col items-center justify-center h-full p-12 text-slate-500 space-y-4">
                <div className="relative">
                  <div className="h-16 w-16 rounded-full border-4 border-blue-200 border-t-blue-600 animate-spin"></div>
                  <ScanLine className="absolute inset-0 m-auto h-6 w-6 text-blue-600" />
                </div>
                <p className="font-medium animate-pulse">Hệ thống TrOCR đang xử lý hình ảnh...</p>
              </div>
            ) : results.length > 0 ? (
              <div className="divide-y divide-slate-100">
                {results.map((item, idx) => (
                  <div key={idx} className="p-4 hover:bg-blue-50 transition-colors flex items-start space-x-4">
                    <div className="flex-shrink-0 h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold">
                      {idx + 1}
                    </div>
                    <div className="flex-1 space-y-1">
                      <p className="text-lg font-semibold text-slate-800 break-words">{item.text}</p>
                      <p className="text-xs text-slate-400 font-mono">
                        Tọa độ: [{item.box.x}, {item.box.y}] • Kích thước: {item.box.width}x{item.box.height}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full p-12 text-slate-400">
                <ScanLine className="h-16 w-16 mb-4 opacity-20" />
                <p className="text-center">Tải ảnh và nhấn "Quét Văn Bản" để xem kết quả hoạt động của model OCR.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
