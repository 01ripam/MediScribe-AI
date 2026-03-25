import NextAuth, { NextAuthOptions } from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import GithubProvider from "next-auth/providers/github";
import CredentialsProvider from "next-auth/providers/credentials";
import { MongoDBAdapter } from "@auth/mongodb-adapter";
import clientPromise from "@/lib/mongodb";

export const authOptions: NextAuthOptions = {
  adapter: MongoDBAdapter(clientPromise) as any,
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_ID || "dummy",
      clientSecret: process.env.GOOGLE_SECRET || "dummy",
    }),
    GithubProvider({
      clientId: process.env.GITHUB_ID || "dummy",
      clientSecret: process.env.GITHUB_SECRET || "dummy",
    }),
    // Included so you can immediately test login without setting up OAuth keys
    CredentialsProvider({
      name: "Demo Account",
      credentials: {
        username: { label: "Username (type 'admin')", type: "text", placeholder: "admin" },
        password: { label: "Password (type 'password')", type: "password", placeholder: "password" }
      },
      async authorize(credentials) {
        if (credentials?.username === "admin" && credentials?.password === "password") {
          // Hardcoded DOCTOR role for the admin demo account
          return { id: "test-admin-id", name: "Dr. Admin", email: "admin@mediscribe.com", role: "DOCTOR" };
        }
        return null;
      }
    })
  ],
  // JWT session strategy is required when using CredentialsProvider with an Adapter
  session: { strategy: "jwt" },
  secret: process.env.NEXTAUTH_SECRET || "fallback_secret_for_development_only_change_this",
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.role = (user as any).role || "PATIENT"; // Default OAuth users to PATIENT
        token.email = user.email;

        // Step 3: The Magic Link (Retroactive Patient Record Association)
        // If this is a patient logging in (indicated by user object existing on signin),
        // scan the Consultations table for matching emails and link them.
        if (token.role === "PATIENT" && user.email && user.id) {
          try {
            const client = await clientPromise;
            const db = client.db();
            // Update all records that belong to this email but haven't been linked yet.
            // We use 'patients' collection for now based on previous steps, but we treat them as Consultations.
            await db.collection("patients").updateMany(
              { patientEmail: user.email, patientUserId: { $exists: false } },
              { $set: { patientUserId: user.id } }
            );
          } catch (err) {
            console.error("Magic link processing failed:", err);
          }
        }
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        (session.user as any).id = token.id;
        (session.user as any).role = token.role || "PATIENT";
      }
      return session;
    }
  },
  // We can customize pages here if we want a fancy login screen, 
  // but for now NextAuth default works well out of the box.
};

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
