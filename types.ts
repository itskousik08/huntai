export enum UserRole {
  USER = 'USER',
  ADMIN = 'ADMIN'
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  credits: number;
  plan: string;
  joinedAt: string;
}

export interface Lead {
  id: string;
  businessName: string;
  category: string;
  location: string;
  phone?: string;
  website?: string;
  email?: string;
  description?: string;
}

export interface GenerationLog {
  id: string;
  userId: string;
  query: {
    location: string;
    category: string;
    quantity: number;
  };
  timestamp: string;
  leadsFound: number;
  creditsUsed: number;
}

export interface Plan {
  id: string;
  name: string;
  credits: number;
  price: number;
  isActive: boolean;
}

export interface SearchResult {
  leads: Lead[];
  groundingMetadata?: any;
}