import React, { useState } from 'react';
import { Send, AlertCircle, Loader2, Sparkles } from 'lucide-react';
import { nlRegistrationService } from '../services/nlRegistrationService';
import { useAuth } from '../context/AuthContext';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';
import { Badge } from './ui/badge';

interface NLRegistrationPanelProps {
    termId?: string;
    onPlansGenerated?: (plans: any[]) => void;
    context?: any;
}

export const NLRegistrationPanel: React.FC<NLRegistrationPanelProps> = ({ termId = "", onPlansGenerated, context }) => {
    const { user } = useAuth();
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [advice, setAdvice] = useState<string | null>(null);
    const [state, setState] = useState<'idle' | 'clarifying'>('idle');
    const [parseResult, setParseResult] = useState<any>(null);
    const [clarifications, setClarifications] = useState<Record<string, number>>({});

    const handleParse = async () => {
        if (!input.trim() || !user) return;
        setLoading(true);
        setError(null);
        setState('idle');
        try {
            const result = await nlRegistrationService.parseIntent({
                student_id: user.id,
                text: input,
                context: {
                    term_id_default: termId,
                    ...(context || {})
                }
            });
            setParseResult(result);

            // Filter: only show clarification items that have candidates
            const actionableItems = result.course_resolution?.needs_clarification?.filter(
                (item: any) => item.candidates && item.candidates.length > 0
            ) || [];

            const notFoundItems = result.course_resolution?.needs_clarification?.filter(
                (item: any) => item.reason === 'not_found' || !item.candidates || item.candidates.length === 0
            ) || [];

            if (notFoundItems.length > 0) {
                const names = notFoundItems.map((i: any) => `"${i.query}"`).join(', ');
                setError(`Không tìm thấy môn: ${names}. Vui lòng kiểm tra lại tên môn.`);
            }

            if (actionableItems.length > 0) {
                setState('clarifying');
            } else if (result.course_resolution?.resolved?.length > 0) {
                // All resolved, auto execute
                handleExecute(result);
            } else if (notFoundItems.length > 0) {
                // Only not_found items, nothing to do
            } else {
                handleExecute(result);
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to parse request");
        } finally {
            setLoading(false);
        }
    };

    const handleExecute = async (parsedData: any = parseResult) => {
        setLoading(true);
        setError(null);
        try {
            const result = await nlRegistrationService.executePlan({
                student_id: user?.id || "1",
                parsed: parsedData,
                clarification_answers: Object.keys(clarifications).length > 0 ? clarifications : undefined
            });

            // Pass plans up to PlannerPage for rendering in Optimization Plan cards
            if (onPlansGenerated && result.plans) {
                onPlansGenerated(result.plans);
            }

            if (result.advice) {
                setAdvice(result.advice);
            } else if (result.plans && result.plans.length === 0 && parsedData?.intent !== 'ADVICE' && parsedData?.intent !== 'EXPORT_ICS') {
                setError("Rất tiếc, không tìm thấy kế hoạch học tập nào đáp ứng được yêu cầu của bạn. Vui lòng điều chỉnh lại điều kiện.");
                setAdvice(null);
            } else {
                setAdvice(null);
            }

            setState('idle');
            setClarifications({});
        } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to execute plan");
        } finally {
            setLoading(false);
        }
    };

    const selectClarification = (query: string, courseId: number) => {
        setClarifications(prev => ({ ...prev, [query]: courseId }));
    };

    return (
        <div className="flex flex-col h-full space-y-4">
            <Card className="border-none shadow-none bg-transparent">
                <CardHeader className="px-0 pt-0">
                    <CardTitle>Đăng ký môn học (Beta)</CardTitle>
                    <CardDescription>
                        Nhập mong muốn của bạn bằng tiếng Việt. Ví dụ: "Đăng ký Giải phẫu và Sinh lý, tránh thứ 7."
                    </CardDescription>
                </CardHeader>
                <CardContent className="px-0">
                    <div className="flex gap-2">
                        <Input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Nhập yêu cầu đăng ký..."
                            onKeyDown={(e) => e.key === 'Enter' && handleParse()}
                            disabled={loading}
                        />
                        <Button onClick={handleParse} disabled={loading || !input.trim()}>
                            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {advice && (
                <Alert className="bg-blue-50 border-blue-100">
                    <Sparkles className="h-4 w-4 text-blue-600" />
                    <AlertTitle className="text-blue-800 font-bold">Tư vấn Học thuật</AlertTitle>
                    <AlertDescription className="text-blue-700 whitespace-pre-wrap">
                        {advice}
                    </AlertDescription>
                </Alert>
            )}

            {error && (
                <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Lỗi</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                </Alert>
            )}

            {state === 'clarifying' && parseResult && (
                <Card>
                    <CardHeader>
                        <CardTitle className="text-sm font-medium">Cần làm rõ thông tin</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {parseResult.course_resolution.needs_clarification
                            .filter((item: any) => item.candidates && item.candidates.length > 0)
                            .map((item: any, idx: number) => (
                                <div key={idx} className="space-y-2">
                                    <p className="text-sm">Bạn muốn đăng ký môn nào cho "<strong>{item.query}</strong>"?</p>
                                    <div className="flex flex-wrap gap-2">
                                        {item.candidates.map((cand: any) => (
                                            <Badge
                                                key={cand.course_id}
                                                variant={clarifications[item.query] === cand.course_id ? "default" : "outline"}
                                                className="cursor-pointer hover:bg-primary/90"
                                                onClick={() => selectClarification(item.query, cand.course_id)}
                                            >
                                                {cand.course_name} ({cand.course_code})
                                            </Badge>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        <Button onClick={() => handleExecute()} disabled={loading} className="w-full">
                            Tiếp tục
                        </Button>
                    </CardContent>
                </Card>
            )}
        </div>
    );
};
