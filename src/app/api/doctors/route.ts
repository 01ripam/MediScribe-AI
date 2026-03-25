import { NextResponse } from 'next/server';

export async function GET() {
  const mockDoctors = [
    { id: "test-admin-id", name: "Dr. Admin", specialty: "General Practice", email: "admin@mediscribe.com" },
    { id: "doc-2", name: "Dr. Sarah Chen", specialty: "Cardiology", email: "schen@mediscribe.com" },
    { id: "doc-3", name: "Dr. Marcus Johnson", specialty: "Neurology", email: "mjohnson@mediscribe.com" },
    { id: "doc-4", name: "Dr. Emily Patel", specialty: "Pediatrics", email: "epatel@mediscribe.com" }
  ];
  return NextResponse.json(mockDoctors);
}
