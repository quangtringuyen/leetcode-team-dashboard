import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authApi } from '@/services/api';
import { useAuthStore } from '@/stores/authStore';
import type { LoginRequest, RegisterRequest } from '@/types';

export function useAuth() {
  const queryClient = useQueryClient();
  const { setToken, setUser, logout: logoutStore } = useAuthStore();

  // Get current user
  const { data: user, isLoading } = useQuery({
    queryKey: ['currentUser'],
    queryFn: authApi.getCurrentUser,
    retry: false,
    enabled: !!localStorage.getItem('access_token'),
  });

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: async (data) => {
      setToken(data.access_token);

      // Fetch user data after login
      const user = await authApi.getCurrentUser();
      setUser(user);

      // Invalidate queries to refetch with new auth
      queryClient.invalidateQueries();
    },
  });

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: async (user) => {
      setUser(user);
    },
  });

  // Logout function
  const logout = () => {
    logoutStore();
    queryClient.clear();
    window.location.href = '/login';
  };

  return {
    user,
    isLoading,
    isAuthenticated: !!localStorage.getItem('access_token'),
    login: (data: LoginRequest) => loginMutation.mutateAsync(data),
    register: (data: RegisterRequest) => registerMutation.mutateAsync(data),
    logout,
    isLoginLoading: loginMutation.isPending,
    isRegisterLoading: registerMutation.isPending,
    loginError: loginMutation.error,
    registerError: registerMutation.error,
  };
}
