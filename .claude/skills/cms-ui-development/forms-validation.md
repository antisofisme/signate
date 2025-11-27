# Forms & Validation Standards

Complete guide for form handling with React Hook Form + Zod.

## Required Dependencies

```json
{
  "dependencies": {
    "react-hook-form": "^7.x",
    "@hookform/resolvers": "^3.x",
    "zod": "^3.x"
  }
}
```

## Core Concepts

### 1. Zod Schema = Single Source of Truth
- Define validation schema ONCE with Zod
- Infer TypeScript types from schema
- Use schema in form AND API validation

### 2. React Hook Form for Performance
- Uncontrolled inputs (minimal re-renders)
- Built-in validation integration
- Form state management (isDirty, isValid, isSubmitting)

---

## Basic Form Template

```typescript
/**
 * FeatureForm - Create/Edit form with RHF + Zod
 */
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslation } from 'react-i18next';
import { Button } from '@/shared/components/ui/button';
import { FormInput } from '@/shared/components/form/FormInput';
import { FormTextarea } from '@/shared/components/form/FormTextarea';
import { FormSwitch } from '@/shared/components/form/FormSwitch';
import { Loader2 } from 'lucide-react';

// 1. Define Zod Schema
const featureSchema = z.object({
  name: z
    .string()
    .min(1, 'Name is required')
    .max(200, 'Name must be less than 200 characters'),
  description: z
    .string()
    .max(2000, 'Description must be less than 2000 characters')
    .optional()
    .nullable(),
  is_active: z.boolean().default(true),
});

// 2. Infer TypeScript Type from Schema
type FeatureFormData = z.infer<typeof featureSchema>;

// 3. Define Props
interface FeatureFormProps {
  feature?: Feature | null;
  onSubmit: (data: FeatureFormData) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

// 4. Component
export function FeatureForm({
  feature,
  onSubmit,
  onCancel,
  isLoading = false,
}: FeatureFormProps) {
  const { t } = useTranslation();
  const isEditing = !!feature;

  // 5. Initialize Form with Schema
  const methods = useForm<FeatureFormData>({
    resolver: zodResolver(featureSchema),
    defaultValues: {
      name: feature?.name || '',
      description: feature?.description || '',
      is_active: feature?.is_active ?? true,
    },
  });

  const {
    handleSubmit,
    formState: { isDirty, isValid },
  } = methods;

  // 6. Handle Submit
  const onFormSubmit = (data: FeatureFormData) => {
    onSubmit(data);
  };

  return (
    <FormProvider {...methods}>
      <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
        {/* Name Field */}
        <FormInput
          name="name"
          label={t('features.form.name')}
          placeholder={t('features.form.namePlaceholder')}
          required
          disabled={isLoading}
        />

        {/* Description Field */}
        <FormTextarea
          name="description"
          label={t('features.form.description')}
          placeholder={t('features.form.descriptionPlaceholder')}
          rows={4}
          maxLength={2000}
          disabled={isLoading}
        />

        {/* Active Toggle */}
        <FormSwitch
          name="is_active"
          label={t('features.form.isActive')}
          description={t('features.form.isActiveDescription')}
          disabled={isLoading}
        />

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t">
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={isLoading}
          >
            {t('common.cancel')}
          </Button>
          <Button
            type="submit"
            disabled={isLoading || !isDirty}
          >
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isEditing ? t('common.update') : t('common.create')}
          </Button>
        </div>
      </form>
    </FormProvider>
  );
}
```

---

## Common Zod Schemas

### Base Schemas (Reusable)

```typescript
// cms-vite/src/shared/validation/schemas.ts

import { z } from 'zod';

// String schemas
export const nameSchema = z
  .string()
  .min(1, 'Name is required')
  .max(200, 'Name must be less than 200 characters')
  .transform((val) => val.trim());

export const descriptionSchema = z
  .string()
  .max(2000, 'Description must be less than 2000 characters')
  .optional()
  .nullable()
  .transform((val) => val?.trim() || null);

export const emailSchema = z
  .string()
  .email('Invalid email format')
  .min(1, 'Email is required');

export const passwordSchema = z
  .string()
  .min(8, 'Password must be at least 8 characters')
  .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
  .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
  .regex(/[0-9]/, 'Password must contain at least one number');

export const usernameSchema = z
  .string()
  .min(3, 'Username must be at least 3 characters')
  .max(50, 'Username must be less than 50 characters')
  .regex(/^[a-zA-Z0-9_]+$/, 'Username can only contain letters, numbers, and underscores');

// Number schemas
export const positiveIntSchema = z.coerce
  .number()
  .int('Must be a whole number')
  .positive('Must be positive');

export const durationSchema = z.coerce
  .number()
  .int()
  .min(1, 'Duration must be at least 1 second')
  .max(86400, 'Duration must be at most 24 hours');

// Boolean schemas
export const isActiveSchema = z.boolean().default(true);

// Date schemas
export const dateSchema = z.coerce.date();

export const futureDateSchema = z.coerce
  .date()
  .refine((date) => date > new Date(), 'Date must be in the future');

// ID schemas
export const idSchema = z.coerce.number().int().positive();

export const optionalIdSchema = z.coerce.number().int().positive().optional().nullable();
```

### Entity-Specific Schemas

```typescript
// Device schema
export const deviceSchema = z.object({
  device_name: nameSchema,
  device_type: z.enum(['tv', 'monitor'], {
    required_error: 'Device type is required',
  }),
  room_number: z.string().max(50).optional().nullable(),
  location_type: z.enum(['guest_room', 'lobby', 'conference_room', 'restaurant', 'other']).default('guest_room'),
  rotation: z.coerce.number().refine((val) => [0, 90, 180, 270].includes(val), {
    message: 'Rotation must be 0, 90, 180, or 270',
  }).default(0),
  is_volume_enabled: z.boolean().default(true),
  is_personalization_supported: z.boolean().default(true),
  privacy_mode: z.enum(['none', 'limited', 'full']).default('limited'),
});

// Content schema
export const contentSchema = z.object({
  title: nameSchema,
  description: descriptionSchema,
  duration: durationSchema,
  is_active: isActiveSchema,
});

// Playlist schema
export const playlistSchema = z.object({
  name: nameSchema,
  description: descriptionSchema,
  is_active: isActiveSchema,
  items: z.array(z.object({
    content_id: idSchema,
    order: positiveIntSchema,
    duration: durationSchema.optional(),
  })).optional(),
});

// User schema
export const createUserSchema = z.object({
  username: usernameSchema,
  email: emailSchema,
  password: passwordSchema,
  full_name: nameSchema,
  role_id: idSchema,
  is_active: isActiveSchema,
});

export const updateUserSchema = createUserSchema.partial().omit({ password: true });

// Password change schema
export const changePasswordSchema = z.object({
  current_password: z.string().min(1, 'Current password is required'),
  new_password: passwordSchema,
  confirm_password: z.string().min(1, 'Please confirm your password'),
}).refine((data) => data.new_password === data.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
});
```

---

## Advanced Patterns

### 1. Conditional Fields

```typescript
const scheduleSchema = z.object({
  name: nameSchema,
  schedule_type: z.enum(['always', 'time_range', 'day_of_week']),
  // Conditional fields based on schedule_type
  start_time: z.string().optional(),
  end_time: z.string().optional(),
  days: z.array(z.number().min(0).max(6)).optional(),
}).superRefine((data, ctx) => {
  if (data.schedule_type === 'time_range') {
    if (!data.start_time) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Start time is required for time range schedule',
        path: ['start_time'],
      });
    }
    if (!data.end_time) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'End time is required for time range schedule',
        path: ['end_time'],
      });
    }
  }
  if (data.schedule_type === 'day_of_week') {
    if (!data.days || data.days.length === 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'At least one day must be selected',
        path: ['days'],
      });
    }
  }
});
```

### 2. Dynamic Form with useFieldArray

```typescript
import { useForm, useFieldArray, FormProvider } from 'react-hook-form';

const playlistItemsSchema = z.object({
  items: z.array(z.object({
    content_id: idSchema,
    duration: durationSchema.optional(),
  })).min(1, 'At least one item is required'),
});

type PlaylistItemsData = z.infer<typeof playlistItemsSchema>;

function PlaylistItemsForm() {
  const methods = useForm<PlaylistItemsData>({
    resolver: zodResolver(playlistItemsSchema),
    defaultValues: { items: [] },
  });

  const { fields, append, remove, move } = useFieldArray({
    control: methods.control,
    name: 'items',
  });

  return (
    <FormProvider {...methods}>
      <form>
        {fields.map((field, index) => (
          <div key={field.id} className="flex gap-4">
            <FormSelect
              name={`items.${index}.content_id`}
              label="Content"
              options={contentOptions}
            />
            <FormInput
              name={`items.${index}.duration`}
              label="Duration (s)"
              type="number"
            />
            <Button
              type="button"
              variant="ghost"
              onClick={() => remove(index)}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        ))}
        <Button
          type="button"
          variant="outline"
          onClick={() => append({ content_id: 0, duration: 10 })}
        >
          <Plus className="mr-2 h-4 w-4" />
          Add Item
        </Button>
      </form>
    </FormProvider>
  );
}
```

### 3. Form with File Upload

```typescript
const contentUploadSchema = z.object({
  title: nameSchema,
  description: descriptionSchema,
  file: z
    .instanceof(File, { message: 'File is required' })
    .refine((file) => file.size <= 50 * 1024 * 1024, 'File must be less than 50MB')
    .refine(
      (file) => ['image/jpeg', 'image/png', 'video/mp4', 'audio/mpeg'].includes(file.type),
      'Unsupported file type'
    ),
});

function ContentUploadForm() {
  const methods = useForm<z.infer<typeof contentUploadSchema>>({
    resolver: zodResolver(contentUploadSchema),
  });

  const { register, setValue, watch } = methods;
  const selectedFile = watch('file');

  return (
    <FormProvider {...methods}>
      <form>
        <FormInput name="title" label="Title" required />
        <FormTextarea name="description" label="Description" />

        {/* File Input */}
        <div className="space-y-2">
          <Label>File</Label>
          <Input
            type="file"
            accept="image/*,video/*,audio/*"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) setValue('file', file);
            }}
          />
          {selectedFile && (
            <p className="text-sm text-muted-foreground">
              Selected: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
            </p>
          )}
        </div>
      </form>
    </FormProvider>
  );
}
```

### 4. Form with API Error Handling

```typescript
function FeatureForm({ onSuccess }: { onSuccess: () => void }) {
  const methods = useForm<FeatureFormData>({
    resolver: zodResolver(featureSchema),
  });

  const { setError } = methods;
  const { create, isCreating } = useFeatureMutations();

  const onSubmit = (data: FeatureFormData) => {
    create(data, {
      onSuccess: () => {
        onSuccess();
      },
      onError: (error: any) => {
        // Handle API validation errors
        if (error.response?.data?.errors) {
          const apiErrors = error.response.data.errors;

          // Set field-specific errors from API
          Object.entries(apiErrors).forEach(([field, message]) => {
            setError(field as keyof FeatureFormData, {
              type: 'server',
              message: message as string,
            });
          });
        } else {
          // Set root error for general API errors
          setError('root', {
            type: 'server',
            message: error.response?.data?.message || 'An error occurred',
          });
        }
      },
    });
  };

  return (
    <FormProvider {...methods}>
      <form onSubmit={methods.handleSubmit(onSubmit)}>
        {/* Root error display */}
        {methods.formState.errors.root && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {methods.formState.errors.root.message}
          </div>
        )}

        {/* Form fields... */}
      </form>
    </FormProvider>
  );
}
```

### 5. Form Reset on Success

```typescript
function FeatureForm() {
  const methods = useForm<FeatureFormData>({
    resolver: zodResolver(featureSchema),
    defaultValues: DEFAULT_VALUES,
  });

  const { reset } = methods;
  const { create } = useFeatureMutations();

  const onSubmit = (data: FeatureFormData) => {
    create(data, {
      onSuccess: () => {
        // Reset form to default values
        reset(DEFAULT_VALUES);
        toast.success('Created successfully');
      },
    });
  };

  return (/* form JSX */);
}
```

---

## Form State Helpers

```typescript
// Access form state
const {
  formState: {
    isDirty,        // Form has been modified
    isValid,        // All fields pass validation
    isSubmitting,   // Form is being submitted
    isSubmitted,    // Form has been submitted at least once
    errors,         // Validation errors
    dirtyFields,    // Which fields have been modified
    touchedFields,  // Which fields have been touched
  },
} = useForm();

// Disable submit button correctly
<Button
  type="submit"
  disabled={isSubmitting || !isDirty}
>
  {isSubmitting ? 'Saving...' : 'Save'}
</Button>

// Show unsaved changes warning
useEffect(() => {
  const handleBeforeUnload = (e: BeforeUnloadEvent) => {
    if (isDirty) {
      e.preventDefault();
      e.returnValue = '';
    }
  };

  window.addEventListener('beforeunload', handleBeforeUnload);
  return () => window.removeEventListener('beforeunload', handleBeforeUnload);
}, [isDirty]);
```

---

## Validation Error Display

### Field-Level Errors

```typescript
// Using FormInput component (auto-displays errors)
<FormInput name="email" label="Email" />

// Manual error display
{errors.email && (
  <p className="text-sm text-destructive">{errors.email.message}</p>
)}
```

### Form-Level Errors

```typescript
// Display at top of form
{Object.keys(errors).length > 0 && (
  <div className="rounded-md bg-destructive/10 p-4 text-sm text-destructive space-y-1">
    <p className="font-medium">Please fix the following errors:</p>
    <ul className="list-disc list-inside">
      {Object.entries(errors).map(([field, error]) => (
        <li key={field}>{error?.message}</li>
      ))}
    </ul>
  </div>
)}
```

---

## Common Mistakes to Avoid

### 1. Forgetting FormProvider
```typescript
// WRONG - fields won't work
<form>
  <FormInput name="name" />
</form>

// CORRECT - wrap with FormProvider
<FormProvider {...methods}>
  <form>
    <FormInput name="name" />
  </form>
</FormProvider>
```

### 2. Not Using Transform for Strings
```typescript
// WRONG - whitespace not trimmed
name: z.string().min(1)

// CORRECT - trim whitespace
name: z.string().min(1).transform(val => val.trim())
```

### 3. Coerce for Number Inputs
```typescript
// WRONG - HTML inputs return strings
duration: z.number()

// CORRECT - coerce string to number
duration: z.coerce.number()
```

### 4. Not Handling Optional vs Nullable
```typescript
// Optional = can be undefined
description: z.string().optional()

// Nullable = can be null
description: z.string().nullable()

// Both = can be undefined OR null
description: z.string().optional().nullable()
```
