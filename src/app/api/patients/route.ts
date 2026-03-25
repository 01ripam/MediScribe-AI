import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '../auth/[...nextauth]/route';
import clientPromise from '@/lib/mongodb';

export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session || !session.user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const client = await clientPromise;
    const db = client.db(); // uses default db from URI
    // Role-based retrieval (Strict Data Isolation)
    const role = (session.user as any).role || 'PATIENT';
    const userId = (session.user as any).id;

    let query = {};
    if (role === 'DOCTOR') {
      // Doctors see all patients they've created (supporting legacy migration userId)
      query = { $or: [{ doctorId: userId }, { userId: userId }] };
    } else {
      // Patients strictly see only their officially linked records
      query = { patientUserId: userId };
    }

    const patients = await db
      .collection('patients')
      .find(query)
      .sort({ date: -1 }) // newest first
      .toArray();

    return NextResponse.json(patients);
  } catch (error) {
    console.error('Error reading patients from DB:', error);
    return NextResponse.json({ error: 'Database error' }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session || !session.user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const newRecord = await req.json();
    const client = await clientPromise;
    const db = client.db();
    if (!newRecord.patientEmail) {
      return NextResponse.json({ error: 'Patient Email is strictly required to securely link the record' }, { status: 400 });
    }

    // Attempt to automatically discover if this patient already exists in our system
    const existingPatient = await db.collection('users').findOne({ email: newRecord.patientEmail, role: 'PATIENT' });
    
    // Create new patient record securely mapped
    const patientEntry = {
      ...newRecord,
      doctorId: (session.user as any).id,
      patientEmail: newRecord.patientEmail,
      patientUserId: existingPatient ? existingPatient._id.toString() : null, // The magic link at insertion time
      date: new Date().toISOString(),
    };
    
    const result = await db.collection('patients').insertOne(patientEntry);
    
    // We can map _id to id for frontend compatibility
    const savedPatient = { ...patientEntry, id: result.insertedId.toString() };
    delete (savedPatient as any)._id;

    return NextResponse.json({ success: true, patient: savedPatient });
  } catch (error: any) {
    console.error('API Error saving patient to DB:', error);
    return NextResponse.json({ error: error.message || 'Error saving patient' }, { status: 500 });
  }
}
