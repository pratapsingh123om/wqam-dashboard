export interface User {
  id: number;
  username: string;
  role: 'admin' | 'validator' | 'user' | 'business' | 'plant';
  is_active: boolean;
}
