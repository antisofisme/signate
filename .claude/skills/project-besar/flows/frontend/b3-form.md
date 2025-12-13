---
description: Create form for PROJECT_BESAR
---

# Flow B3: Create Form

> **Standards**: STD-02 (Validation), STD-15 (Input Design Flow & Constraint-Based UI)
>
> **Key Principle**: Make it impossible to enter wrong data. Use dropdowns/selects instead of text, disable fields based on context, show cascading options, provide real-time feedback.

## Pre-requisites
- [ ] Form fields defined with constraint rules (required, optional, conditional, cascading)
- [ ] Validation rules defined (backend Pydantic + frontend Zod)
- [ ] API endpoint ready
- [ ] Dependencies documented (which fields enable/disable others, which dropdowns depend on parent selections)

## Step 1: Create Zod Schema
Location: `modules/{module}/frontend/src/schemas/{entity}.schema.ts`

```typescript
import { z } from 'zod';

export const {entity}Schema = z.object({
  name: z.string().min(1, 'Required').max(100),
  email: z.string().email('Invalid email'),
  // Add fields
});

export type {Entity}FormData = z.infer<typeof {entity}Schema>;
```

## Step 2: Create Form Component
Location: `modules/{module}/frontend/src/components/{Entity}Form/{Entity}Form.tsx`

```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { {entity}Schema, {Entity}FormData } from '@/schemas/{entity}.schema';

interface {Entity}FormProps {
  defaultValues?: Partial<{Entity}FormData>;
  onSubmit: (data: {Entity}FormData) => void;
}

export const {Entity}Form: FC<{Entity}FormProps> = ({
  defaultValues,
  onSubmit,
}) => {
  const form = useForm<{Entity}FormData>({
    resolver: zodResolver({entity}Schema),
    defaultValues,
  });

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      <FormField
        control={form.control}
        name="name"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Name</FormLabel>
            <FormControl>
              <Input {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <Button type="submit">Submit</Button>
    </form>
  );
};
```

## Step 3: Handle Submission
```typescript
const { mutate, isPending } = use{Entity}Mutation();

const handleSubmit = (data: {Entity}FormData) => {
  mutate(data, {
    onSuccess: () => {
      toast.success('Saved successfully');
      router.push('/{entities}');
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });
};
```

## Advanced: Cascading & Conditional Fields (STD-15)

If form has dependent fields:

```typescript
// Example: COA creation with cascading type → sub_type
const [selectedType, setSelectedType] = useState<CoaType | null>(null);
const [subTypeOptions, setSubTypeOptions] = useState([]);

const handleTypeChange = async (type: CoaType) => {
  setSelectedType(type);

  // Fetch sub-types for this type
  const subtypes = await api.getCoASubTypes(type);
  setSubTypeOptions(subtypes);

  // Clear sub_type field
  form.setValue('sub_type', '');
};

// In form: sub_type field disabled until type selected
<FormField
  control={form.control}
  name="sub_type"
  render={({ field }) => (
    <FormItem>
      <FormLabel>Sub Type</FormLabel>
      <Select
        disabled={!selectedType}  // Disabled until parent selected
        onValueChange={field.onChange}
        value={field.value}
      >
        <SelectContent>
          {subTypeOptions.map(opt => (
            <SelectItem key={opt.value} value={opt.value}>
              {opt.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {!selectedType && (
        <FormDescription>Select account type first</FormDescription>
      )}
      <FormMessage />
    </FormItem>
  )}
/>
```

## Checklist Before Complete
- [ ] Zod schema matches backend Pydantic
- [ ] All required fields marked with * (visible in UI)
- [ ] Error messages are actionable (not just "Invalid!")
- [ ] Cascading fields: parent → child dependencies enforced
- [ ] Conditional fields: shown/hidden based on form state
- [ ] Dropdowns used instead of text for predefined values
- [ ] Disabled states prevent impossible combinations
- [ ] Loading state shown during submission
- [ ] Success/error feedback provided
- [ ] Help text explains each field's purpose
- [ ] Form prevents invalid combinations at UI level
