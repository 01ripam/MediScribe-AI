import { NextResponse } from 'next/server';
import clientPromise from '@/lib/mongodb';
import { getServerSession } from 'next-auth';
import { authOptions } from '../auth/[...nextauth]/route';

export async function GET(req: Request) {
  try {
    const session = await getServerSession(authOptions);
    if (!session?.user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const role = (session.user as any).role;
    const client = await clientPromise;
    const db = client.db();
    let query: any = {};

    if (role === 'DOCTOR') {
      // Doctors see only reports assigned to them that are marked as Emergency
      query = { doctorId: (session.user as any).id, isEmergency: true };
    } else {
      // Patients see all their own reports
      query = { patientEmail: session.user.email };
    }

    const reports = await db.collection('reports').find(query).sort({ createdAt: -1 }).toArray();
    return NextResponse.json(reports);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch reports' }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const session = await getServerSession(authOptions);
    if (!session?.user || (session.user as any).role !== 'PATIENT') {
      return NextResponse.json({ error: 'Unauthorized or not a patient' }, { status: 401 });
    }

    const body = await req.json();
    const client = await clientPromise;
    const db = client.db();

    const result = await db.collection('reports').insertOne({
      patientEmail: session.user.email,
      patientName: session.user.name,
      doctorId: body.doctorId, 
      aiSummary: body.aiSummary,
      isEmergency: body.isEmergency,
      details: body.details,
      rawText: body.rawText,
      createdAt: new Date().toISOString(),
      status: 'UNREAD'
    });

    return NextResponse.json({ id: result.insertedId });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to create report' }, { status: 500 });
  }
}
