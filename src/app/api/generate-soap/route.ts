import { GoogleGenAI } from '@google/genai';
import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '../auth/[...nextauth]/route';

export async function POST(req: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    if (!session || !session.user) {
      return NextResponse.json({ error: 'Unauthorized. Please login.' }, { status: 401 });
    }

    const formData = await req.formData();
    const audioFile = formData.get('audio') as File | null;
    let transcript = formData.get('transcript') as string | null;
    let userApiKey = formData.get('apiKey') as string | null;

    if (!audioFile && !transcript) {
      return NextResponse.json({ error: 'No audio or transcript provided' }, { status: 400 });
    }

    const apiKey = userApiKey || process.env.GEMINI_API_KEY;

    if (!apiKey) {
      return NextResponse.json({ error: 'No Gemini API Key found. Please add it to your environment or input it directly on the app.' }, { status: 401 });
    }

    // Initialize Gemini SDK with the key
    const ai = new GoogleGenAI({ apiKey });

    const systemInstruction = `You are an expert medical scribe. Analyze the provided consultation data.
    Extract the following patient demographic details if mentioned: Name, Age, Gender, Blood Group.
    Then, generate a highly professional, well-structured clinical SOAP note from it. Focus strictly on medical facts.
    
    You MUST output valid JSON exactly matching this structure:
    {
      "name": "Extracted name or ''",
      "age": "Extracted age or ''",
      "gender": "Extracted gender or ''",
      "bloodGroup": "Extracted blood group or ''",
      "subjective": "Self-reported symptoms, history of present illness...",
      "objective": "Doctor's observations, vitals...",
      "assessment": "Diagnosis and reasoning...",
      "plan": "Treatment, follow-up..."
    }`;

    let payloadParts: any[] = [{ text: systemInstruction }];

    if (transcript) {
      // If a pure text transcript is provided dynamically
      payloadParts.push({ text: `TRANSCRIPT DATA:\n\n${transcript}` });
    } else if (audioFile) {
      // Convert File to Base64
      const arrayBuffer = await audioFile.arrayBuffer();
      const buffer = Buffer.from(arrayBuffer);
      const base64Audio = buffer.toString('base64');
      const mimeType = audioFile.type || 'audio/webm';
      payloadParts.push({ 
        inlineData: {
          data: base64Audio,
          mimeType: mimeType
        } 
      });
    }

    // Call the latest Gemini Flash which natively supports audio alongside text context
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: [{ role: 'user', parts: payloadParts }],
      config: {
        responseMimeType: "application/json"
      }
    });

    const resultText = response.text || '{}';
    let parsedResult;
    try {
      parsedResult = JSON.parse(resultText);
    } catch (e) {
      console.error("Failed to parse JSON from AI:", resultText);
      parsedResult = { subjective: resultText, name: '', age: '', gender: '', bloodGroup: '' };
    }

    return NextResponse.json(parsedResult);
  } catch (error: any) {
    console.error('API Error:', error);
    return NextResponse.json({ error: error.message || 'Internal Server Error while process audio' }, { status: 500 });
  }
}
