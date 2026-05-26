import api from './api';

export interface NLParseRequest {
    student_id: string;
    text: string;
    context?: any;
}

export interface NLExecuteRequest {
    student_id: string;
    parsed: any;
    clarification_answers?: Record<string, number>;
}

export const nlRegistrationService = {
    parseIntent: async (data: NLParseRequest) => {
        const response = await api.post('/v1/nl/register/parse', data);
        return response.data;
    },

    executePlan: async (data: NLExecuteRequest) => {
        const response = await api.post('/v1/nl/register/execute', data);
        return response.data;
    }
};
