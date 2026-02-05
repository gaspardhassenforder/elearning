'use client'

import { useState } from 'react'
import { AppShell } from '@/components/layout/AppShell'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
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
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { useCompanies, useCreateCompany, useUpdateCompany, useDeleteCompany } from '@/lib/hooks/use-companies'
import { useTranslation } from '@/lib/hooks/use-translation'
import { CompanyResponse, CreateCompanyRequest, UpdateCompanyRequest } from '@/lib/types/api'
import { Plus, Pencil, Trash2, RefreshCw, Search, Building2, Users, Boxes } from 'lucide-react'

export default function CompaniesPage() {
  const { t } = useTranslation()
  const { data: companies, isLoading, refetch } = useCompanies()
  const createCompany = useCreateCompany()
  const updateCompany = useUpdateCompany()
  const deleteCompany = useDeleteCompany()

  const [searchQuery, setSearchQuery] = useState('')
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [selectedCompany, setSelectedCompany] = useState<CompanyResponse | null>(null)

  // Form state
  const [formData, setFormData] = useState<CreateCompanyRequest>({
    name: '',
    slug: '',
    description: '',
  })

  const filteredCompanies = companies?.filter(
    (company) =>
      company.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      company.slug.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const resetForm = () => {
    setFormData({
      name: '',
      slug: '',
      description: '',
    })
  }

  const handleCreate = async () => {
    await createCompany.mutateAsync(formData)
    setIsCreateDialogOpen(false)
    resetForm()
  }

  const handleEdit = (company: CompanyResponse) => {
    setSelectedCompany(company)
    setFormData({
      name: company.name,
      slug: company.slug,
      description: company.description || '',
    })
    setIsEditDialogOpen(true)
  }

  const handleUpdate = async () => {
    if (!selectedCompany) return
    const updateData: UpdateCompanyRequest = {
      name: formData.name,
      slug: formData.slug,
      description: formData.description || undefined,
    }
    await updateCompany.mutateAsync({ id: selectedCompany.id, data: updateData })
    setIsEditDialogOpen(false)
    setSelectedCompany(null)
    resetForm()
  }

  const handleDeleteClick = (company: CompanyResponse) => {
    setSelectedCompany(company)
    setIsDeleteDialogOpen(true)
  }

  const handleDelete = async () => {
    if (!selectedCompany) return
    await deleteCompany.mutateAsync(selectedCompany.id)
    setIsDeleteDialogOpen(false)
    setSelectedCompany(null)
  }

  // Auto-generate slug from name
  const handleNameChange = (name: string) => {
    setFormData({
      ...formData,
      name,
      slug: name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, ''),
    })
  }

  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <Building2 className="h-6 w-6" />
                {t.companies.title}
              </h1>
              <p className="text-muted-foreground mt-1">{t.companies.subtitle}</p>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => refetch()}>
                <RefreshCw className="h-4 w-4" />
              </Button>
              <Button onClick={() => setIsCreateDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                {t.companies.createCompany}
              </Button>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={t.companies.searchPlaceholder}
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
          ) : filteredCompanies && filteredCompanies.length > 0 ? (
            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t.companies.name}</TableHead>
                    <TableHead>{t.companies.slug}</TableHead>
                    <TableHead>{t.companies.description}</TableHead>
                    <TableHead>{t.companies.userCount}</TableHead>
                    <TableHead>{t.companies.assignmentCount}</TableHead>
                    <TableHead className="text-right">{t.common.actions}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredCompanies.map((company) => (
                    <TableRow key={company.id}>
                      <TableCell className="font-medium">{company.name}</TableCell>
                      <TableCell>
                        <code className="text-sm bg-muted px-1.5 py-0.5 rounded">
                          {company.slug}
                        </code>
                      </TableCell>
                      <TableCell className="max-w-xs truncate">
                        {company.description || '-'}
                      </TableCell>
                      <TableCell>
                        <Badge variant={company.user_count > 0 ? "default" : "secondary"} className="gap-1">
                          <Users className="h-3 w-3" />
                          {company.user_count > 0 ? company.user_count : t.companies.noLearners}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={company.assignment_count > 0 ? "outline" : "secondary"} className="gap-1">
                          <Boxes className="h-3 w-3" />
                          {company.assignment_count > 0 ? company.assignment_count : t.companies.noModules}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEdit(company)}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteClick(company)}
                          disabled={company.user_count > 0 || company.assignment_count > 0}
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
              <Building2 className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
              <h3 className="text-lg font-medium">{t.companies.noCompanies}</h3>
              <p className="text-muted-foreground mt-1">{t.companies.noCompaniesDescription}</p>
              <Button className="mt-4" onClick={() => setIsCreateDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                {t.companies.createCompany}
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Create Company Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t.companies.createCompany}</DialogTitle>
            <DialogDescription>
              {t.companies.subtitle}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">{t.companies.name}</Label>
              <Input
                id="name"
                placeholder={t.companies.namePlaceholder}
                value={formData.name}
                onChange={(e) => handleNameChange(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="slug">{t.companies.slug}</Label>
              <Input
                id="slug"
                placeholder={t.companies.slugPlaceholder}
                value={formData.slug}
                onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
              />
              <p className="text-xs text-muted-foreground">{t.companies.slugHint}</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">{t.companies.description}</Label>
              <Textarea
                id="description"
                placeholder={t.companies.descriptionPlaceholder}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
              {t.common.cancel}
            </Button>
            <Button
              onClick={handleCreate}
              disabled={createCompany.isPending || !formData.name || !formData.slug}
            >
              {createCompany.isPending ? t.common.creating : t.common.create}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Company Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t.companies.editCompany}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-name">{t.companies.name}</Label>
              <Input
                id="edit-name"
                placeholder={t.companies.namePlaceholder}
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-slug">{t.companies.slug}</Label>
              <Input
                id="edit-slug"
                placeholder={t.companies.slugPlaceholder}
                value={formData.slug}
                onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
              />
              <p className="text-xs text-muted-foreground">{t.companies.slugHint}</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-description">{t.companies.description}</Label>
              <Textarea
                id="edit-description"
                placeholder={t.companies.descriptionPlaceholder}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              {t.common.cancel}
            </Button>
            <Button
              onClick={handleUpdate}
              disabled={updateCompany.isPending || !formData.name || !formData.slug}
            >
              {updateCompany.isPending ? t.common.saving : t.common.save}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Company Dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t.companies.deleteCompany}</DialogTitle>
            <DialogDescription>
              {(() => {
                const hasUsers = selectedCompany?.user_count && selectedCompany.user_count > 0
                const hasAssignments = selectedCompany?.assignment_count && selectedCompany.assignment_count > 0
                if (hasUsers && hasAssignments) {
                  return t.companies.reassignFirst
                } else if (hasUsers) {
                  return t.companies.deleteWithUsersError
                } else if (hasAssignments) {
                  return t.companies.deleteWithAssignmentsError
                }
                return t.companies.deleteConfirm
              })()}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeleteDialogOpen(false)}>
              {t.common.cancel}
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={
                deleteCompany.isPending ||
                Boolean(selectedCompany?.user_count && selectedCompany.user_count > 0) ||
                Boolean(selectedCompany?.assignment_count && selectedCompany.assignment_count > 0)
              }
            >
              {deleteCompany.isPending ? t.common.deleting : t.common.delete}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppShell>
  )
}
