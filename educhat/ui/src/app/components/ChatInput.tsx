import { Send, Paperclip, Mic, Camera, Loader2, ScanLine } from "lucide-react";
import type { KeyboardEvent } from "react";
import { useEffect, useRef, useState } from "react";
import { cn } from "../utils/cn";
import { apiService } from "../services/apiService";

interface ChatInputProps {
	onSendMessage: (message: string) => void;
	disabled: boolean;
}

export default function ChatInput({ onSendMessage, disabled }: ChatInputProps) {
	const [inputValue, setInputValue] = useState("");
	const textareaRef = useRef<HTMLTextAreaElement>(null);
	const fileInputRef = useRef<HTMLInputElement>(null);
	const [isFocused, setIsFocused] = useState(false);
	const [isScanning, setIsScanning] = useState(false);

	const handleSend = () => {
		const trimmedValue = inputValue.trim();
		if (trimmedValue && !disabled) {
			onSendMessage(trimmedValue);
			setInputValue("");
			// Reset height
			if (textareaRef.current) {
				textareaRef.current.style.height = "auto";
			}
		}
	};

	const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
		if (e.key === "Enter" && !e.shiftKey) {
			e.preventDefault();
			handleSend();
		}
	};

	const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
		if (e.target.files && e.target.files.length > 0) {
			const file = e.target.files[0];
			setIsScanning(true);
			try {
				const response = await apiService.scanOCRImage(file);
				if (response && response.data) {
					// Nối tất cả các cụm chữ lấy được thành một đoạn văn bản
					const extractedText = response.data.map((item: any) => item.text).join(" ");
					setInputValue(prev => prev ? `${prev} ${extractedText}` : extractedText);
				}
			} catch (error) {
				console.error("Lỗi khi quét ảnh OCR:", error);
				alert("Không thể quét ảnh. Hãy chắc chắn rằng bạn đã bật OCR Microservice (python ocr_server.py).");
			} finally {
				setIsScanning(false);
				if (fileInputRef.current) {
					fileInputRef.current.value = "";
				}
				if (textareaRef.current) {
					textareaRef.current.focus();
				}
			}
		}
	};

	// Web Speech API Integration
	const [isListening, setIsListening] = useState(false);
	const recognitionRef = useRef<any>(null);

	useEffect(() => {
		// Khởi tạo Speech Recognition nếu trình duyệt hỗ trợ
		const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
		if (SpeechRecognition) {
			const recognition = new SpeechRecognition();
			recognition.continuous = true;
			recognition.interimResults = true;
			recognition.lang = 'vi-VN'; // Mặc định nhận dạng tiếng Việt

			recognition.onresult = (event: any) => {
				let interimTranscript = '';
				let finalTranscript = '';

				for (let i = event.resultIndex; i < event.results.length; ++i) {
					if (event.results[i].isFinal) {
						finalTranscript += event.results[i][0].transcript;
					} else {
						interimTranscript += event.results[i][0].transcript;
					}
				}

				// Ghi nhận kết quả
				if (finalTranscript) {
					setInputValue((prev) => prev ? `${prev} ${finalTranscript}` : finalTranscript);
				}
			};

			recognition.onerror = (event: any) => {
				console.error("Speech recognition error", event.error);
				setIsListening(false);
			};

			recognition.onend = () => {
				setIsListening(false);
			};

			recognitionRef.current = recognition;
		}
	}, []);

	const toggleListening = () => {
		if (isListening) {
			recognitionRef.current?.stop();
			setIsListening(false);
		} else {
			if (recognitionRef.current) {
				try {
					recognitionRef.current.start();
					setIsListening(true);
				} catch (e) {
					console.error(e);
				}
			} else {
				alert("Trình duyệt của bạn không hỗ trợ nhận dạng giọng nói. Vui lòng sử dụng Chrome/Edge.");
			}
		}
	};

	// Document File API Integration
	const docFileInputRef = useRef<HTMLInputElement>(null);
	
	const handleDocFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
		if (e.target.files && e.target.files.length > 0) {
			const file = e.target.files[0];
			
			// Giới hạn dung lượng file < 5MB để tránh treo trình duyệt
			if (file.size > 5 * 1024 * 1024) {
				alert("Vui lòng chọn file có dung lượng dưới 5MB.");
				return;
			}

			// Đọc trực tiếp các file dạng văn bản tại trình duyệt
			if (file.name.endsWith('.txt') || file.name.endsWith('.csv') || file.name.endsWith('.json') || file.name.endsWith('.md')) {
				const reader = new FileReader();
				reader.onload = (event) => {
					const text = event.target?.result as string;
					if (text) {
						setInputValue((prev) => prev ? `${prev}\n\n[Nội dung file ${file.name}]:\n${text}` : `[Nội dung file ${file.name}]:\n${text}`);
					}
				};
				reader.readAsText(file);
			} else {
				alert(`Hệ thống hiện tại đang hỗ trợ đọc văn bản từ ảnh (OCR) và file text (txt, csv, json). Đối với file PDF hoặc Word, bạn sẽ cần phát triển thêm luồng RAG ở Backend!`);
			}
			
			if (docFileInputRef.current) {
				docFileInputRef.current.value = "";
			}
		}
	};

	// Auto-resize textarea
	useEffect(() => {
		if (textareaRef.current) {
			textareaRef.current.style.height = "auto";
			const scrollHeight = textareaRef.current.scrollHeight;
			textareaRef.current.style.height = `${Math.min(scrollHeight, 120)}px`;
		}
	}, [inputValue]);

	return (
		<div className="border-t border-slate-200 bg-white px-4 py-4">
			<div className={cn(
				"max-w-4xl mx-auto bg-white rounded-lg border transition-colors duration-200",
				isFocused ? "border-slate-500 ring-2 ring-slate-100" : "border-slate-200 hover:border-slate-300"
			)}>
				<div className="flex items-end gap-2 p-2">
					
					{/* Input File Ẩn cho Document */}
					<input 
						type="file" 
						accept=".txt,.csv,.json,.md" 
						className="hidden" 
						ref={docFileInputRef} 
						onChange={handleDocFileChange} 
					/>

					{/* Icon đính kèm File */}
					<button
						type="button"
						onClick={() => docFileInputRef.current?.click()}
						className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-md transition-colors relative"
						disabled={disabled || isScanning || isListening}
						title="Đính kèm tài liệu (TXT, CSV, JSON)"
					>
						<Paperclip size={20} />
					</button>

					{/* Input File Ẩn cho OCR */}
					<input 
						type="file" 
						accept="image/*" 
						className="hidden" 
						ref={fileInputRef} 
						onChange={handleFileChange} 
					/>
					
					{/* Icon quét ảnh giống Google Lens */}
					<button
						type="button"
						onClick={() => fileInputRef.current?.click()}
						className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors relative"
						disabled={disabled || isScanning || isListening}
						title="Quét chữ từ hình ảnh (OCR)"
					>
						{isScanning ? (
							<Loader2 size={20} className="animate-spin text-blue-600" />
						) : (
							<ScanLine size={20} />
						)}
					</button>

					<textarea
						ref={textareaRef}
						value={inputValue}
						onChange={(e) => setInputValue(e.target.value)}
						onKeyDown={handleKeyDown}
						onFocus={() => setIsFocused(true)}
						onBlur={() => setIsFocused(false)}
						placeholder={
							isScanning ? "Đang dùng AI quét chữ..." : 
							isListening ? "Đang nghe... Hãy nói đi" : 
							"Nhập câu hỏi hoặc gửi ảnh..."
						}
						disabled={disabled || isScanning}
						rows={1}
						className={cn(
							"flex-1 bg-transparent px-2 py-3 focus:outline-none resize-none max-h-32 text-slate-900 placeholder-slate-400",
							isListening && "animate-pulse text-red-600 font-medium placeholder-red-400"
						)}
						style={{ minHeight: "44px" }}
					/>

					{/* Icon Ghi âm Speech-to-Text */}
					{!inputValue.trim() && (
						<button
							type="button"
							onClick={toggleListening}
							className={cn(
								"p-2 rounded-md transition-colors",
								isListening 
									? "text-red-500 bg-red-50 hover:bg-red-100 animate-pulse" 
									: "text-slate-400 hover:text-slate-700 hover:bg-slate-100"
							)}
							disabled={disabled || isScanning}
							title="Nói để nhập văn bản (Speech-to-Text)"
						>
							<Mic size={20} />
						</button>
					)}

					<button
						type="button"
						onClick={handleSend}
						disabled={disabled || !inputValue.trim() || isScanning}
						className={cn(
							"p-2 rounded-md flex items-center justify-center transition-colors duration-200",
							inputValue.trim() && !disabled && !isScanning
								? "bg-slate-900 text-white hover:bg-slate-700"
								: "bg-slate-100 text-slate-400 cursor-not-allowed"
						)}
						aria-label="Send message"
					>
						<Send size={20} className={inputValue.trim() ? "ml-0.5" : ""} />
					</button>
				</div>
			</div>

			<p className="text-xs text-center mt-3 text-slate-400 font-medium">
				Agent có thể mắc sai sót. Hãy kiểm tra lại thông tin quan trọng.
			</p>
		</div>
	);
}
