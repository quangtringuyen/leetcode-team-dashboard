// TypeScript interfaces matching your FastAPI backend

export interface User {
  username: string;
  email: string;
  full_name?: string | null;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface TeamMember {
  username: string;
  name: string;
  avatar?: string | null;
  totalSolved: number;
  ranking?: number | null;
  easy: number;
  medium: number;
  hard: number;
  status?: string;
}

export interface AddMemberRequest {
  username: string;
  name: string;
  avatar?: string;
}

export interface TeamStats {
  totalMembers: number;
  totalSolved: number;
  averageSolved: number;
  topSolver: {
    username: string;
    totalSolved: number;
  } | null;
  total_problems_solved: number;
  difficulty_breakdown: {
    easy: number;
    medium: number;
    hard: number;
  };
}

export interface WeeklySnapshot {
  week_start: string;
  member: string;
  totalSolved: number;
  easy: number;
  medium: number;
  hard: number;
}

export interface TrendData {
  weeks: string[];
  members: {
    [member: string]: {
      week: string;
      total: number;
      easy: number;
      medium: number;
      hard: number;
    }[];
  };
}

export interface WeekOverWeekChange {
  week: string;
  member: string;
  previous: number;
  current: number;
  change: number;
  pct_change: number;
  rank: number;
  rank_delta: number;
}

export interface SnapshotResponse {
  message: string;
  count: number;
  week_start: string;
  members_updated: number;
}

export interface ApiError {
  detail: string;
}

export interface WeeklyProgressData {
  weeks: string[];
  members: {
    [username: string]: {
      name: string;
      data: number[];
    };
  };
}

export interface AcceptedTrendData {
  date: string;
  member: string;
  username: string;
  accepted: number;
}

export interface DailyChallenge {
  date: string;
  link: string;
  questionId: string;
  title: string;
  titleSlug: string;
  difficulty: string;
}

export interface RecentSubmission {
  title: string;
  titleSlug: string;
  timestamp: string;
  date: string; // formatted date or timestamp
  username: string;
  name: string;
  avatar?: string;
  accepted: number;
}

export interface DailyChallengeCompletion {
  username: string;
  name: string;
  avatar: string | null;
  completionTime: string;
}

export interface DailyChallengeHistory {
  date: string;
  title: string;
  titleSlug: string;
  difficulty: string;
  link: string;
  completions: DailyChallengeCompletion[];
  completedCount: number;
  totalMembers: number;
}

export interface DailyChallengeHistoryResponse {
  history: DailyChallengeHistory[];
  totalMembers: number;
}
