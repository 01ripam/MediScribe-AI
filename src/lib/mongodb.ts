/**
 * Utility to connect to MongoDB and cache the client promise
 * Required by NextAuth MongoDB Adapter for reusing the connection
 */
import { MongoClient } from 'mongodb';

if (!process.env.MONGODB_URI) {
  // If no URI is provided, use a default local instance for development,
  // or throw an error. For zero-setup, we default to localhost.
  console.warn('MONGODB_URI is not set. Defaulting to mongodb://localhost:27017/mediscribe');
}

const uri = process.env.MONGODB_URI || 'mongodb://localhost:27017/mediscribe';
const options = {};

let client: MongoClient;
let clientPromise: Promise<MongoClient>;

if (process.env.NODE_ENV === 'development') {
  let globalWithMongo = global as typeof globalThis & {
    _mongoClientPromise?: Promise<MongoClient>;
  };

  if (!globalWithMongo._mongoClientPromise) {
    client = new MongoClient(uri, options);
    globalWithMongo._mongoClientPromise = client.connect();
  }
  clientPromise = globalWithMongo._mongoClientPromise;
} else {
  client = new MongoClient(uri, options);
  clientPromise = client.connect();
}

export default clientPromise;
