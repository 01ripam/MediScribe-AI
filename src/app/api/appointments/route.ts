import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '../auth/[...nextauth]/route';
import clientPromise from '@/lib/mongodb';

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const mode = searchParams.get('mode');

  // --- PUBLIC AVAILABILITY MODE (no auth required, for patient booking UI) ---
  if (mode === 'availability') {
    const doctorId = searchParams.get('doctorId');
    const month = searchParams.get('month'); // e.g. "2026-03"
    if (!doctorId || !month) {
      return NextResponse.json({ error: 'doctorId and month required' }, { status: 400 });
    }
    try {
      const client = await clientPromise;
      const db = client.db();
      const startOfMonth = new Date(`${month}-01T00:00:00.000Z`);
      const endOfMonth = new Date(startOfMonth);
      endOfMonth.setMonth(endOfMonth.getMonth() + 1);

      const booked = await db.collection('appointments').find({
        doctorId,
        status: 'UPCOMING',
        appointmentDate: {
          $gte: startOfMonth.toISOString(),
          $lt: endOfMonth.toISOString(),
        }
      }).project({ appointmentDate: 1, _id: 0 }).toArray();

      return NextResponse.json(booked.map(a => a.appointmentDate));
    } catch (error) {
      return NextResponse.json({ error: 'Database error' }, { status: 500 });
    }
  }

  // --- AUTHENTICATED DOCTOR VIEW ---
  const session = await getServerSession(authOptions);
  if (!session || !session.user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const role = (session.user as any).role;
  if (role !== 'DOCTOR') {
    return NextResponse.json({ error: 'Only Doctors can access the appointment schedule' }, { status: 403 });
  }

  const doctorId = (session.user as any).id;
  const statusFilter = searchParams.get('status');
  // Optional: filter by specific calendar month (YYYY-MM)
  const calendarMonth = searchParams.get('month');

  try {
    const client = await clientPromise;
    const db = client.db();

    const query: any = { doctorId };
    if (statusFilter) {
      query.status = statusFilter;
    }
    if (calendarMonth) {
      const start = new Date(`${calendarMonth}-01T00:00:00.000Z`);
      const end = new Date(start);
      end.setMonth(end.getMonth() + 1);
      query.appointmentDate = { $gte: start.toISOString(), $lt: end.toISOString() };
    }

    const sortOrder = statusFilter === 'UPCOMING' ? 1 : -1;
    const appointments = await db
      .collection('appointments')
      .find(query)
      .sort({ appointmentDate: sortOrder })
      .toArray();

    const mapped = appointments.map(a => ({ ...a, id: a._id.toString(), _id: undefined }));
    return NextResponse.json(mapped);
  } catch (error) {
    console.error('Error reading appointments from DB:', error);
    return NextResponse.json({ error: 'Database error' }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session || !session.user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const role = (session.user as any).role;
  if (role !== 'DOCTOR' && role !== 'PATIENT') {
    return NextResponse.json({ error: 'Unauthorized role' }, { status: 403 });
  }

  try {
    const newRecord = await req.json();
    const client = await clientPromise;
    const db = client.db();

    if (!newRecord.appointmentDate) {
      return NextResponse.json({ error: 'Missing required appointment date' }, { status: 400 });
    }

    const patientName = role === 'PATIENT' ? (session.user?.name || 'Patient') : newRecord.patientName;
    const patientEmail = role === 'PATIENT' ? (session.user?.email || '') : newRecord.patientEmail;
    const doctorId = role === 'PATIENT' ? (newRecord.doctorId || '') : (session.user as any).id;

    if (!patientName || !patientEmail) {
      return NextResponse.json({ error: 'Missing patient information' }, { status: 400 });
    }
    if (!doctorId) {
      return NextResponse.json({ error: 'Missing doctorId' }, { status: 400 });
    }

    // ---- DOUBLE-BOOKING PREVENTION ----
    // Reject if doctor already has an UPCOMING appointment within ±30 minutes of the requested time
    const requestedTime = new Date(newRecord.appointmentDate);
    const windowMs = 30 * 60 * 1000;
    const windowStart = new Date(requestedTime.getTime() - windowMs).toISOString();
    const windowEnd = new Date(requestedTime.getTime() + windowMs).toISOString();

    const conflict = await db.collection('appointments').findOne({
      doctorId,
      status: 'UPCOMING',
      appointmentDate: { $gt: windowStart, $lt: windowEnd }
    });

    if (conflict) {
      const conflictTime = new Date(conflict.appointmentDate).toLocaleTimeString([], {
        hour: '2-digit', minute: '2-digit'
      });
      return NextResponse.json(
        {
          error: `Dr. is already booked at ${conflictTime}. Appointments must be at least 30 minutes apart. Please choose a different time.`
        },
        { status: 409 }
      );
    }
    // ---- END DOUBLE-BOOKING PREVENTION ----

    const appointmentEntry = {
      patientName,
      patientEmail,
      patientAge: newRecord.patientAge || '',
      patientGender: newRecord.patientGender || '',
      appointmentDate: requestedTime.toISOString(),
      status: 'UPCOMING',
      doctorId,
      consultationId: null,
      createdAt: new Date().toISOString(),
    };

    const result = await db.collection('appointments').insertOne(appointmentEntry);
    const saved = { ...appointmentEntry, id: result.insertedId.toString() };
    return NextResponse.json({ success: true, appointment: saved });
  } catch (error: any) {
    console.error('API Error saving appointment to DB:', error);
    return NextResponse.json({ error: error.message || 'Error saving appointment' }, { status: 500 });
  }
}
