export interface LoginResponse {
    user_id: string;
    email: string;
    created_at: string;
}

export interface UserSession {
    user_id: string;
    email: string;
    full_name: string | null;
    avatar_url: string | null;
}
