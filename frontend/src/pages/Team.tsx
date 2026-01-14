import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { UserPlus, Trash2, Users, Download, Upload, Database, Pencil } from 'lucide-react';
import { useTeam } from '@/hooks/useTeam';
import { teamApi } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import type { AddMemberRequest } from '@/types';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { DEFAULT_AVATAR } from '@/lib/constants';

const addMemberSchema = z.object({
  username: z.string().min(1, 'LeetCode username is required'),
  name: z.string().min(1, 'Display name is required'),
  avatar: z.string().url('Must be a valid URL').optional().or(z.literal('')),
});

export default function Team() {
  const { members, addMember, removeMember, isMembersLoading, isAddingMember, isRemovingMember } =
    useTeam();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Edit State
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [editingMember, setEditingMember] = useState<any>(null);
  const [editFormData, setEditFormData] = useState({ name: '', username: '', status: 'active' });
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<AddMemberRequest>({
    resolver: zodResolver(addMemberSchema),
  });

  const onSubmit = async (data: AddMemberRequest) => {
    try {
      setError(null);
      setSuccess(null);
      await addMember(data);
      setSuccess(`${data.name} has been added to the team!`);
      reset();
      setIsDialogOpen(false);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add member');
    }
  };

  const handleRemoveMember = async (username: string, name: string) => {
    if (!confirm(`Are you sure you want to remove ${name} from the team?`)) {
      return;
    }

    try {
      await removeMember(username);
      setSuccess(`${name} has been removed from the team.`);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to remove member');
    }
  };

  const handleExportExcel = async () => {
    try {
      const blob = await teamApi.exportExcel();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `team-data-${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      setSuccess('Team data exported to Excel successfully!');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to export data');
    }
  };

  const handleBackup = async () => {
    try {
      const data = await teamApi.backup();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `team-backup-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      setSuccess('Backup downloaded successfully!');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create backup');
    }
  };

  const handleRestore = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const backup = JSON.parse(text);
      await teamApi.restore(backup);
      setSuccess('Data restored successfully! Refreshing...');
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to restore backup. Please check the file format.');
    }
  };

  // Update member mutation
  const updateMember = useMutation({
    mutationFn: async (data: { currentUsername: string; name: string; username: string; status: string }) => {
      await teamApi.updateMember(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['team-members'] });
      toast.success('Member updated successfully');
      setIsEditOpen(false);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update member');
    },
  });

  const handleEditClick = (member: any) => {
    setEditingMember(member);
    setEditFormData({ name: member.name, username: member.username, status: member.status || 'active' });
    setIsEditOpen(true);
  };

  const handleEditSave = async () => {
    if (!editFormData.username) return;

    await updateMember.mutateAsync({
      currentUsername: editingMember.username,
      name: editFormData.name,
      username: editFormData.username,
      status: editFormData.status
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold gradient-text">Team Management</h1>
          <p className="text-muted-foreground mt-1">
            Add, remove, and manage your team members
          </p>
        </div>

        <div className="flex gap-2">
          <Button variant="outline" className="gap-2" onClick={handleExportExcel}>
            <Download className="h-4 w-4" />
            Export to Excel
          </Button>

          <Button variant="outline" className="gap-2" onClick={handleBackup}>
            <Database className="h-4 w-4" />
            Download Backup
          </Button>

          <label htmlFor="restore-file">
            <Button variant="outline" className="gap-2" asChild>
              <span>
                <Upload className="h-4 w-4" />
                Upload Restore
              </span>
            </Button>
            <input
              id="restore-file"
              type="file"
              accept=".json"
              className="hidden"
              onChange={handleRestore}
            />
          </label>

          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2">
                <UserPlus className="h-4 w-4" />
                Add Member
              </Button>
            </DialogTrigger>
            <DialogContent className="glass">
              <DialogHeader>
                <DialogTitle>Add Team Member</DialogTitle>
                <DialogDescription>
                  Add a new member by their LeetCode username
                </DialogDescription>
              </DialogHeader>

              <form onSubmit={handleSubmit(onSubmit)}>
                <div className="space-y-4 py-4">
                  {error && (
                    <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm">
                      {error}
                    </div>
                  )}

                  <div className="space-y-2">
                    <label htmlFor="username" className="text-sm font-medium">
                      LeetCode Username
                    </label>
                    <Input
                      id="username"
                      placeholder="e.g., john_doe"
                      {...register('username')}
                      className={errors.username ? 'border-destructive' : ''}
                    />
                    {errors.username && (
                      <p className="text-sm text-destructive">{errors.username.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="name" className="text-sm font-medium">
                      Display Name
                    </label>
                    <Input
                      id="name"
                      placeholder="e.g., John Doe"
                      {...register('name')}
                      className={errors.name ? 'border-destructive' : ''}
                    />
                    {errors.name && (
                      <p className="text-sm text-destructive">{errors.name.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="avatar" className="text-sm font-medium">
                      Avatar URL <span className="text-muted-foreground">(optional)</span>
                    </label>
                    <Input
                      id="avatar"
                      type="url"
                      placeholder="https://example.com/avatar.jpg"
                      {...register('avatar')}
                      className={errors.avatar ? 'border-destructive' : ''}
                    />
                    {errors.avatar && (
                      <p className="text-sm text-destructive">{errors.avatar.message}</p>
                    )}
                  </div>
                </div>

                <DialogFooter>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setIsDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={isAddingMember}>
                    {isAddingMember ? 'Adding...' : 'Add Member'}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Edit Member Dialog */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Member</DialogTitle>
            <DialogDescription>
              Update member details. If Name is left blank, the Username will be displayed.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label htmlFor="edit-status" className="text-sm font-medium">Status</label>
              <select
                id="edit-status"
                value={editFormData.status}
                onChange={(e) => setEditFormData({ ...editFormData, status: e.target.value })}
                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              >
                <option value="active">Active</option>
                <option value="suspended">Suspended</option>
              </select>
              <p className="text-xs text-muted-foreground">
                Suspended members will not appear in analytics or charts but their data is preserved.
              </p>
            </div>
            <div className="space-y-2">
              <label htmlFor="edit-name" className="text-sm font-medium">Display Name</label>
              <Input
                id="edit-name"
                value={editFormData.name}
                onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
                placeholder="Enter display name"
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="edit-username" className="text-sm font-medium">LeetCode Username</label>
              <Input
                id="edit-username"
                value={editFormData.username}
                onChange={(e) => setEditFormData({ ...editFormData, username: e.target.value })}
                placeholder="Enter LeetCode username"
              />
              <p className="text-xs text-muted-foreground">
                Changing this will update all historical data to the new username.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleEditSave} disabled={updateMember.isPending}>
              {updateMember.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Success Message */}
      {success && (
        <div className="p-4 rounded-lg bg-primary/10 border border-primary/20 text-primary">
          {success}
        </div>
      )}

      {/* Team Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="glass">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Members</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{members.length}</div>
          </CardContent>
        </Card>
        <Card className="glass">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Members</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {members.filter((m) => m.status !== 'suspended').length}
            </div>
          </CardContent>
        </Card>
        <Card className="glass">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Solved</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {members.reduce((sum, m) => sum + m.totalSolved, 0)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Team Members List */}
      <Card className="glass">
        <CardHeader>
          <CardTitle>Team Members</CardTitle>
          <CardDescription>Manage your team roster</CardDescription>
        </CardHeader>
        <CardContent>
          {isMembersLoading ? (
            <p className="text-muted-foreground">Loading team members...</p>
          ) : members.length === 0 ? (
            <div className="text-center py-12">
              <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">No team members yet</p>
              <p className="text-sm text-muted-foreground mt-1">
                Add your first member to get started
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {members.map((member) => (
                <div
                  key={member.username}
                  className={`flex items-center justify-between p-4 rounded-lg bg-accent/50 hover:bg-accent transition-colors ${member.status === 'suspended' ? 'opacity-60 grayscale-[0.5]' : ''
                    }`}
                >
                  <div className="flex items-center gap-4">
                    <Avatar className="h-12 w-12">
                      <AvatarImage src={member.avatar || DEFAULT_AVATAR} alt={member.name} />
                      <AvatarFallback className="bg-primary/10 text-primary font-semibold text-lg">
                        {member.name.charAt(0).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{member.name}</p>
                        {member.status === 'suspended' && (
                          <Badge variant="destructive" className="text-[10px] px-1 h-5">
                            Suspended
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">@{member.username}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="font-semibold mr-2">
                      {member.totalSolved} solved
                    </Badge>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEditClick(member)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-destructive hover:text-destructive hover:bg-destructive/10"
                      onClick={() => handleRemoveMember(member.username, member.name)}
                      disabled={isRemovingMember}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
