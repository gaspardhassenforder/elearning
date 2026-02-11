'use client'

import { useState } from 'react'
import { AppShell } from '@/components/layout/AppShell'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { useUsers, useCreateUser, useUpdateUser, useDeleteUser } from '@/lib/hooks/use-users'
import { useCompanies } from '@/lib/hooks/use-companies'
import { useTranslation } from '@/lib/hooks/use-translation'
import { UserListResponse, CreateUserRequest, UpdateUserRequest } from '@/lib/types/api'
import { Plus, Pencil, Trash2, RefreshCw, Search, Users } from 'lucide-react'

export default function UsersPage() {
  const { t } = useTranslation()
  const { data: users, isLoading, refetch } = useUsers()
  const { data: companies } = useCompanies()
  const createUser = useCreateUser()
  const updateUser = useUpdateUser()
  const deleteUser = useDeleteUser()

  const [searchQuery, setSearchQuery] = useState('')
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState<UserListResponse | null>(null)

  // Form state
  const [formData, setFormData] = useState<CreateUserRequest>({
    username: '',
    email: '',
    password: '',
    role: 'learner',
    company_id: undefined,
  })

  const filteredUsers = users?.filter(
    (user) =>
      user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (user.company_name && user.company_name.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  const resetForm = () => {
    setFormData({
      username: '',
      email: '',
      password: '',
      role: 'learner',
      company_id: undefined,
    })
  }

  const handleCreate = async () => {
    await createUser.mutateAsync(formData)
    setIsCreateDialogOpen(false)
    resetForm()
  }

  const handleEdit = (user: UserListResponse) => {
    setSelectedUser(user)
    setFormData({
      username: user.username,
      email: user.email,
      password: '',
      role: user.role,
      company_id: user.company_id || undefined,
    })
    setIsEditDialogOpen(true)
  }

  const handleUpdate = async () => {
    if (!selectedUser) return
    const updateData: UpdateUserRequest = {
      username: formData.username,
      email: formData.email,
      role: formData.role,
      company_id: formData.company_id || null,
    }
    if (formData.password) {
      updateData.password = formData.password
    }
    await updateUser.mutateAsync({ id: selectedUser.id, data: updateData })
    setIsEditDialogOpen(false)
    setSelectedUser(null)
    resetForm()
  }

  const handleDeleteClick = (user: UserListResponse) => {
    setSelectedUser(user)
    setIsDeleteDialogOpen(true)
  }

  const handleDelete = async () => {
    if (!selectedUser) return
    await deleteUser.mutateAsync(selectedUser.id)
    setIsDeleteDialogOpen(false)
    setSelectedUser(null)
  }

  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <Users className="h-6 w-6" />
                {t.users.title}
              </h1>
              <p className="text-muted-foreground mt-1">{t.users.subtitle}</p>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => refetch()}>
                <RefreshCw className="h-4 w-4" />
              </Button>
              <Button onClick={() => setIsCreateDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                {t.users.createUser}
              </Button>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={t.users.searchPlaceholder}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>

          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">
              {t.common.loading}
            </div>
          ) : filteredUsers && filteredUsers.length > 0 ? (
            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t.users.username}</TableHead>
                    <TableHead>{t.users.email}</TableHead>
                    <TableHead>{t.users.role}</TableHead>
                    <TableHead>{t.users.company}</TableHead>
                    <TableHead className="text-right">{t.common.actions}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredUsers.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell className="font-medium">{user.username}</TableCell>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>
                        <Badge variant={user.role === 'admin' ? 'default' : 'secondary'}>
                          {user.role === 'admin' ? t.users.admin : t.users.learner}
                        </Badge>
                      </TableCell>
                      <TableCell>{user.company_name || t.users.noCompany}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEdit(user)}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteClick(user)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="text-center py-12 border rounded-lg">
              <Users className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
              <h3 className="text-lg font-medium">{t.users.noUsers}</h3>
              <p className="text-muted-foreground mt-1">{t.users.noUsersDescription}</p>
              <Button className="mt-4" onClick={() => setIsCreateDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                {t.users.createUser}
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Create User Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t.users.createUser}</DialogTitle>
            <DialogDescription>
              {t.users.subtitle}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="username">{t.users.username}</Label>
              <Input
                id="username"
                placeholder={t.users.usernamePlaceholder}
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">{t.users.email}</Label>
              <Input
                id="email"
                type="email"
                placeholder={t.users.emailPlaceholder}
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">{t.users.password}</Label>
              <Input
                id="password"
                type="password"
                placeholder={t.users.passwordPlaceholder}
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="role">{t.users.role}</Label>
              <Select
                value={formData.role}
                onValueChange={(value: 'admin' | 'learner') => setFormData({ ...formData, role: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder={t.users.selectRole} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="learner">{t.users.learner}</SelectItem>
                  <SelectItem value="admin">{t.users.admin}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="company">{t.users.company}</Label>
              <Select
                value={formData.company_id || '__none__'}
                onValueChange={(value) => setFormData({ ...formData, company_id: value === '__none__' ? undefined : value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder={t.users.selectCompany} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__none__">{t.users.noCompany}</SelectItem>
                  {companies?.map((company) => (
                    <SelectItem key={company.id} value={company.id}>
                      {company.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
              {t.common.cancel}
            </Button>
            <Button
              onClick={handleCreate}
              disabled={createUser.isPending || !formData.username || !formData.email || !formData.password}
            >
              {createUser.isPending ? t.common.creating : t.common.create}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit User Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t.users.editUser}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-username">{t.users.username}</Label>
              <Input
                id="edit-username"
                placeholder={t.users.usernamePlaceholder}
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-email">{t.users.email}</Label>
              <Input
                id="edit-email"
                type="email"
                placeholder={t.users.emailPlaceholder}
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-password">{t.users.password}</Label>
              <Input
                id="edit-password"
                type="password"
                placeholder={t.users.passwordPlaceholder}
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              />
              <p className="text-xs text-muted-foreground">{t.users.passwordHint}</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-role">{t.users.role}</Label>
              <Select
                value={formData.role}
                onValueChange={(value: 'admin' | 'learner') => setFormData({ ...formData, role: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder={t.users.selectRole} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="learner">{t.users.learner}</SelectItem>
                  <SelectItem value="admin">{t.users.admin}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-company">{t.users.company}</Label>
              <Select
                value={formData.company_id || '__none__'}
                onValueChange={(value) => setFormData({ ...formData, company_id: value === '__none__' ? undefined : value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder={t.users.selectCompany} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__none__">{t.users.noCompany}</SelectItem>
                  {companies?.map((company) => (
                    <SelectItem key={company.id} value={company.id}>
                      {company.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              {t.common.cancel}
            </Button>
            <Button
              onClick={handleUpdate}
              disabled={updateUser.isPending || !formData.username || !formData.email}
            >
              {updateUser.isPending ? t.common.saving : t.common.save}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete User Dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t.users.deleteUser}</DialogTitle>
            <DialogDescription>{t.users.deleteConfirm}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeleteDialogOpen(false)}>
              {t.common.cancel}
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteUser.isPending}
            >
              {deleteUser.isPending ? t.common.deleting : t.common.delete}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppShell>
  )
}
