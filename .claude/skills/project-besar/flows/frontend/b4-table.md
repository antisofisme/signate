---
description: Create data table for PROJECT_BESAR
---

# Flow B4: Create Data Table

## Pre-requisites
- [ ] Data structure defined
- [ ] Columns identified
- [ ] Actions identified

## Step 1: Define Columns
Location: `modules/{module}/frontend/src/components/{Entity}Table/columns.tsx`

```typescript
import { ColumnDef } from '@tanstack/react-table';
import { {Entity} } from '@/types/{entity}';

export const columns: ColumnDef<{Entity}>[] = [
  {
    accessorKey: 'name',
    header: 'Name',
    cell: ({ row }) => <span>{row.getValue('name')}</span>,
  },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: ({ row }) => <StatusBadge status={row.getValue('status')} />,
  },
  {
    id: 'actions',
    cell: ({ row }) => <RowActions entity={row.original} />,
  },
];
```

## Step 2: Create Table Component
Location: `modules/{module}/frontend/src/components/{Entity}Table/{Entity}Table.tsx`

```typescript
import { DataTable } from '@/components/ui/DataTable';
import { columns } from './columns';
import { use{Entity}ListQuery } from '@/hooks/use{Entity}';

export const {Entity}Table: FC = () => {
  const { data, isLoading } = use{Entity}ListQuery();

  return (
    <DataTable
      columns={columns}
      data={data?.items ?? []}
      isLoading={isLoading}
      pagination={{
        page: data?.meta.page ?? 1,
        pageSize: data?.meta.per_page ?? 20,
        total: data?.meta.total ?? 0,
      }}
    />
  );
};
```

## Step 3: Add Filtering
```typescript
const [filters, setFilters] = useState<{Entity}Filters>({});

<DataTable
  filters={filters}
  onFilterChange={setFilters}
  filterFields={[
    { key: 'status', label: 'Status', type: 'select', options: statusOptions },
    { key: 'search', label: 'Search', type: 'text' },
  ]}
/>
```

## Step 4: Add Row Actions
```typescript
const RowActions: FC<{ entity: {Entity} }> = ({ entity }) => (
  <DropdownMenu>
    <DropdownMenuTrigger asChild>
      <Button variant="ghost" size="icon"><MoreHorizontal /></Button>
    </DropdownMenuTrigger>
    <DropdownMenuContent>
      <DropdownMenuItem onClick={() => router.push(`/{entities}/${entity.id}`)}>
        View
      </DropdownMenuItem>
      <DropdownMenuItem onClick={() => router.push(`/{entities}/${entity.id}/edit`)}>
        Edit
      </DropdownMenuItem>
      <DropdownMenuItem onClick={() => handleDelete(entity.id)} className="text-red-600">
        Delete
      </DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>
);
```

## Checklist Before Complete
- [ ] Columns sortable
- [ ] Filtering works
- [ ] Pagination works
- [ ] Actions work
- [ ] Loading state
