import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '../../auth/[...nextauth]/route';
import clientPromise from '@/lib/mongodb';
import { ObjectId } from 'mongodb';

export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const session = await getServerSession(authOptions);
  if (!session || !session.user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const client = await clientPromise;
    const db = client.db();
    
    const appointment = await db
      .collection('appointments')
      .findOne({ _id: new ObjectId(id), doctorId: (session.user as any).id });

    if (!appointment) return NextResponse.json({ error: 'Appointment not found' }, { status: 404 });

    const mapped = { ...appointment, id: appointment._id.toString(), _id: undefined };
    return NextResponse.json(mapped);
  } catch (error) {
    return NextResponse.json({ error: 'Database error' }, { status: 500 });
  }
}

export async function PATCH(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const session = await getServerSession(authOptions);
  if (!session || !session.user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const body = await req.json();
    const client = await clientPromise;
    const db = client.db();
    
    const updatePayload: any = {};
    if (body.status) updatePayload.status = body.status;
    if (body.consultationId) updatePayload.consultationId = body.consultationId;

    const result = await db.collection('appointments').updateOne(
      { _id: new ObjectId(id), doctorId: (session.user as any).id },
      { $set: updatePayload }
    );

    if (result.matchedCount === 0) {
      return NextResponse.json({ error: 'Appointment not found or unauthorized' }, { status: 404 });
    }

    return NextResponse.json({ success: true });
  } catch (error: any) {
    return NextResponse.json({ error: error.message || 'Error updating appointment' }, { status: 500 });
  }
}
