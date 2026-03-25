import { NextResponse } from 'next/server';
import { GoogleGenAI } from '@google/genai';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const reportText = body.reportText;
    if (!reportText) return NextResponse.json({ error: 'No report text provided' }, { status: 400 });

    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) return NextResponse.json({ error: 'GEMINI_API_KEY not configured' }, { status: 500 });

    const ai = new GoogleGenAI({ apiKey });

    const prompt = `You are an expert AI Triage Nurse. Read the following patient diagnostic report/lab results.
Provide a JSON response with exactly three keys:
- "summary": A concise 2-sentence summary of the key findings.
- "isEmergency": A boolean (true/false). Set this to true ONLY IF the results show life-threatening or highly critical abnormalities that require immediate physician intervention.
- "details": A string with bullet points of the most important abnormal metric values, separated by newlines.

Report Text:
${reportText}`;

    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: [{ role: 'user', parts: [{ text: prompt }] }],
      config: { responseMimeType: 'application/json' }
    });

    const resultText = response.text || '{}';
    const parsed = JSON.parse(resultText);

    return NextResponse.json(parsed);
  } catch (error) {
    console.error("AI Analysis Failed:", error);
    return NextResponse.json({ error: 'Failed to analyze report' }, { status: 500 });
  }
}
