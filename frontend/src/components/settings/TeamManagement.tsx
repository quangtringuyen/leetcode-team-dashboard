import { useState } from 'react';
import { useTeam } from '@/hooks/useTeam';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Pencil, Users } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { toast } from 'sonner';
import { DEFAULT_AVATAR } from '@/lib/constants';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function TeamManagement() {
    const { members } = useTeam();
    const queryClient = useQueryClient();
    const [editingMember, setEditingMember] = useState<any>(null);
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [formData, setFormData] = useState({ name: '', username: '' });

    // Update member mutation
    const updateMember = useMutation({
        mutationFn: async (data: { currentUsername: string; name: string; username: string }) => {
            const token = localStorage.getItem('access_token');
            await axios.put(
                `${API_URL}/members/${data.currentUsername}`,
                { name: data.name, username: data.username },
                { headers: { Authorization: `Bearer ${token}` } }
            );
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['team-members'] });
            toast.success('Member updated successfully');
            setIsDialogOpen(false);
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || 'Failed to update member');
        },
    });

    const handleEdit = (member: any) => {
        setEditingMember(member);
        setFormData({ name: member.name, username: member.username });
        setIsDialogOpen(true);
    };

    const handleSave = async () => {
        if (!formData.username) return;

        await updateMember.mutateAsync({
            currentUsername: editingMember.username,
            name: formData.name,
            username: formData.username
        });
    };

    return (
        <Card className="glass">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Users className="h-5 w-5" />
                    Team Members
                </CardTitle>
                <CardDescription>
                    Manage your team members. You can edit their display name and LeetCode username.
                </CardDescription>
            </CardHeader>
            <CardContent>
                <div className="rounded-md border">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Member</TableHead>
                                <TableHead>LeetCode Username</TableHead>
                                <TableHead className="text-right">Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {members.map((member) => (
                                <TableRow key={member.username}>
                                    <TableCell className="flex items-center gap-2">
                                        <Avatar className="h-8 w-8">
                                            <AvatarImage src={member.avatar || DEFAULT_AVATAR} alt={member.name} />
                                            <AvatarFallback>{member.name[0]}</AvatarFallback>
                                        </Avatar>
                                        <span className="font-medium">{member.name}</span>
                                    </TableCell>
                                    <TableCell>{member.username}</TableCell>
                                    <TableCell className="text-right">
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            onClick={() => handleEdit(member)}
                                        >
                                            <Pencil className="h-4 w-4" />
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </div>

                <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Edit Member</DialogTitle>
                            <DialogDescription>
                                Update member details. If Name is left blank, the Username will be displayed.
                            </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4 py-4">
                            <div className="space-y-2">
                                <Label htmlFor="name">Display Name</Label>
                                <Input
                                    id="name"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    placeholder="Enter display name"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="username">LeetCode Username</Label>
                                <Input
                                    id="username"
                                    value={formData.username}
                                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                                    placeholder="Enter LeetCode username"
                                />
                                <p className="text-xs text-muted-foreground">
                                    Changing this will update all historical data to the new username.
                                </p>
                            </div>
                        </div>
                        <DialogFooter>
                            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
                                Cancel
                            </Button>
                            <Button onClick={handleSave} disabled={updateMember.isPending}>
                                {updateMember.isPending ? 'Saving...' : 'Save Changes'}
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </CardContent>
        </Card>
    );
}
