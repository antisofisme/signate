# Input Design Flow & Constraint-Based UI

> **Standard #40**: Prevent Input Errors Through Guided Workflows & UI Constraints
>
> **Last Updated**: 2025-12-13
> **Status**: ✅ Standard Approved
> **Related**: STD-02 (Validation), STD-12 (Config Governance), SEC-01 (Security)

---

## Overview

**The Principle**: "Make it impossible to enter wrong data rather than detect wrong data after."

This standard establishes patterns for input forms, data master setup workflows, and settings UI to prevent user errors at the point of input. When COA hierarchy is correct, room setup is complete, menu items are properly linked—all downstream processes (journal, reporting, reconciliation) work correctly by default.

---

## 1. Core Principles

### 1.1 Prevention Over Detection

```
┌─────────────────────────────────────────────────────────────┐
│ DETECTION (❌ Expensive)                                     │
│ User enters wrong COA parent → Error message → User confused │
│ → Often leads to workaround → Data integrity issues          │
├─────────────────────────────────────────────────────────────┤
│ PREVENTION (✅ Efficient)                                    │
│ Dropdown only shows valid COA parents → User can't choose   │
│ wrong → Data is correct by default → No reconciliation issues │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Input Design Hierarchy

```
Level 1: Database Constraints
├─ NOT NULL, UNIQUE, FK, CHECK constraints
└─ Last defense, but shouldn't be needed if UI is correct

Level 2: Backend Validation
├─ Pydantic DTOs validate type, format, business rules
└─ Catch client-side attacks, not user mistakes

Level 3: Frontend Real-Time
├─ React Hook Form, Zod validation
├─ Show errors immediately as user types
└─ Enable/disable fields based on context

Level 4: UI Prevention Design ← This standard focuses here
├─ Dropdown instead of text input (can't type wrong)
├─ Cascading fields (parent selection enables child)
├─ Conditional visibility (shows only relevant fields)
└─ Dependency enforcement (complete parent before child)
```

### 1.3 Key Patterns

| Pattern | Problem It Solves | Example |
|---------|-------------------|---------|
| **Dropdown/Select** | User types wrong value | Instead of text "Bank Mandiri", use dropdown with predefined banks |
| **Cascading Fields** | Invalid combinations | After selecting COA type "Asset", only show asset-specific subtype |
| **Conditional Fields** | User forgets to fill related fields | If "Is Branch" = Yes, require "Branch Code" |
| **Disabled State** | Prevents premature entry | "Edit Room Rate" button disabled until room type is selected |
| **Guided Workflow** | Complex setup done in wrong order | COA master must complete parent→type→name in sequence |
| **Dependency Check** | Parent data missing | Can't create "Room Rate" until "Room Type" exists |
| **Preview & Impact** | Settings misconfigured | "Tax Rate" field shows preview of how it affects pricing |
| **Progressive Disclosure** | Overwhelm user with options | Show basic fields first, "Advanced Settings" expandable section |

---

## 2. Form Field Design Patterns

### 2.1 Required vs Optional Fields

```typescript
// DO: Make the requirement visible in UI, not just schema
interface FieldConfig {
  name: string;
  label: string;
  required: boolean;        // Shows * in label
  type: 'text' | 'select' | 'number' | 'date' | 'textarea';
  validation?: {
    minLength?: number;
    maxLength?: number;
    pattern?: string;
    custom?: (value: any) => boolean;
  };
  disabled?: boolean | ((formValues: any) => boolean);
  visible?: boolean | ((formValues: any) => boolean);
  help?: string;            // Contextual help text
  placeholder?: string;
}

// Example: COA Creation Form
const coaFields: FieldConfig[] = [
  {
    name: 'code',
    label: 'COA Code',
    required: true,
    type: 'text',
    validation: { pattern: '^[0-9]{4,6}$' },
    help: 'Format: 4-6 digits (e.g., 1010 for Assets)',
    placeholder: '1010'
  },
  {
    name: 'parent_id',
    label: 'Parent Account',
    required: true,
    type: 'select',
    // Parent list comes from backend, filtered by current COA type
    help: 'Parent account must be defined before creating sub-account'
  },
  {
    name: 'type',
    label: 'Account Type',
    required: true,
    type: 'select',
    // Options: ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE, etc
    help: 'Account type determines allowed sub-types'
  },
  {
    name: 'sub_type',
    label: 'Sub Type',
    required: true,
    type: 'select',
    // OPTIONS CHANGE based on selected 'type'
    visible: (values) => !!values.type, // Only show after type selected
    disabled: (values) => !values.type,
    help: 'Filtered based on account type selected above'
  },
  {
    name: 'name',
    label: 'Account Name',
    required: true,
    type: 'text',
    validation: { minLength: 3, maxLength: 100 }
  },
  {
    name: 'is_header',
    label: 'Is Header Account',
    required: false,
    type: 'checkbox',
    help: 'Header accounts cannot have transactions; only used for grouping'
  },
  {
    name: 'description',
    label: 'Description',
    required: false,
    type: 'textarea',
    validation: { maxLength: 500 }
  }
];
```

### 2.2 Cascading/Dependent Fields

```typescript
// PATTERN: Field visibility/options depend on parent field

interface FormState {
  type: 'ASSET' | 'LIABILITY' | 'EQUITY' | 'REVENUE' | 'EXPENSE' | null;
  sub_type: string;
  parent_id: string;
}

// Rules:
// 1. Type MUST be selected first
// 2. Sub-type options depend on Type
// 3. Parent account must be same type as current account

const formRules = {
  // Rule: sub_type only shows when type is selected
  sub_type: {
    visible: (state) => !!state.type,
    disabled: (state) => !state.type,
    options: (state) => {
      if (!state.type) return [];

      const subTypeMap = {
        ASSET: [
          { value: 'current_asset', label: 'Current Asset' },
          { value: 'fixed_asset', label: 'Fixed Asset' }
        ],
        LIABILITY: [
          { value: 'current_liability', label: 'Current Liability' },
          { value: 'long_term_liability', label: 'Long-Term Liability' }
        ],
        // ... etc
      };

      return subTypeMap[state.type] || [];
    }
  },

  // Rule: parent_id options must match type
  parent_id: {
    visible: true,
    disabled: (state) => !state.type,
    options: async (state) => {
      if (!state.type) return [];

      // Fetch only parents of same type
      const parents = await api.getCOAByType(state.type);
      return parents.map(p => ({
        value: p.id,
        label: `${p.code} - ${p.name}`
      }));
    }
  }
};
```

### 2.3 Conditional Field Visibility

```typescript
// PATTERN: Show/hide field groups based on conditions

interface FormConfig {
  sections: {
    name: string;
    title: string;
    fields: FieldConfig[];
    visible?: (state: any) => boolean;
  }[];
}

// Example: Employee Setup Form with Conditional Sections
const employeeFormConfig: FormConfig = {
  sections: [
    {
      name: 'basic',
      title: 'Basic Information',
      visible: () => true,  // Always shown
      fields: [
        { name: 'first_name', label: 'First Name', required: true, type: 'text' },
        { name: 'last_name', label: 'Last Name', required: true, type: 'text' },
        { name: 'email', label: 'Email', required: true, type: 'text' }
      ]
    },
    {
      name: 'employment',
      title: 'Employment Details',
      fields: [
        { name: 'department_id', label: 'Department', required: true, type: 'select' },
        { name: 'position_id', label: 'Position', required: true, type: 'select' },
        { name: 'employment_type', label: 'Type', required: true, type: 'select',
          options: ['Full-time', 'Part-time', 'Contract'] }
      ]
    },
    {
      name: 'branch_details',
      title: 'Branch Assignment',
      visible: (state) => state.employment_type === 'Full-time',  // Only show for full-time
      fields: [
        { name: 'assigned_branch', label: 'Branch', required: true, type: 'select' },
        { name: 'branch_start_date', label: 'Start Date', required: true, type: 'date' }
      ]
    },
    {
      name: 'manager',
      title: 'Manager Assignment',
      visible: (state) => {
        // Show manager section only for non-manager positions
        return state.position_id && state.position_id !== 'manager';
      },
      fields: [
        { name: 'manager_id', label: 'Direct Manager', required: true, type: 'select' }
      ]
    },
    {
      name: 'bank_details',
      title: 'Bank Account (for Payroll)',
      visible: (state) => state.employment_type !== 'Contract',  // Contract employees get cash
      fields: [
        { name: 'bank_name', label: 'Bank', required: true, type: 'select' },
        { name: 'account_number', label: 'Account Number', required: true, type: 'text' },
        { name: 'account_holder', label: 'Account Holder Name', required: true, type: 'text' }
      ]
    }
  ]
};
```

---

## 3. Data Master Setup Workflows

### 3.1 Guided Workflow Pattern

For complex data (COA, Room Types, Menu Items), use **step-by-step workflow** instead of single form.

#### Example: Chart of Accounts (COA) Setup Workflow

```typescript
// Step-based wizard ensures parent → type → details in correct order

interface CoaSetupStep {
  number: number;
  title: string;
  description: string;
  requiredFields: string[];
  validation: (data: any) => { valid: boolean; errors?: string[] };
  onComplete?: (data: any) => Promise<void>;
}

const coaSetupWorkflow: CoaSetupStep[] = [
  {
    number: 1,
    title: 'Account Hierarchy',
    description: 'Define where this account belongs in the chart',
    requiredFields: ['type', 'parent_id'],
    validation: (data) => {
      const errors = [];
      if (!data.type) errors.push('Account type is required');
      if (!data.parent_id) errors.push('Parent account is required');
      return { valid: errors.length === 0, errors };
    },
    onComplete: async (data) => {
      // Validate parent_id exists and is of same type
      const parent = await api.getCOAById(data.parent_id);
      if (!parent || parent.type !== data.type) {
        throw new Error('Invalid parent account');
      }
    }
  },
  {
    number: 2,
    title: 'Account Details',
    description: 'Enter account code, name, and classification',
    requiredFields: ['code', 'name', 'sub_type'],
    validation: (data) => {
      const errors = [];
      if (!data.code || !/^[0-9]{4,6}$/.test(data.code)) {
        errors.push('Code must be 4-6 digits');
      }
      if (!data.name || data.name.length < 3) {
        errors.push('Name must be at least 3 characters');
      }
      if (!data.sub_type) errors.push('Sub type is required');
      return { valid: errors.length === 0, errors };
    }
  },
  {
    number: 3,
    title: 'Behavioral Properties',
    description: 'Set account behavior and posting rules',
    requiredFields: [],  // All optional
    validation: () => ({ valid: true })
  },
  {
    number: 4,
    title: 'Review & Create',
    description: 'Review the account configuration before saving',
    requiredFields: [],
    validation: (data) => {
      // Final comprehensive validation
      return { valid: true };
    },
    onComplete: async (data) => {
      // Create account in database
      return await api.createCOA(data);
    }
  }
];

// React Component Implementation
function CoaSetupWizard() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({});
  const [errors, setErrors] = useState<string[]>([]);

  const currentStepConfig = coaSetupWorkflow[step - 1];

  const handleNext = async () => {
    const validation = currentStepConfig.validation(formData);

    if (!validation.valid) {
      setErrors(validation.errors || []);
      return;
    }

    if (currentStepConfig.onComplete) {
      try {
        await currentStepConfig.onComplete(formData);
      } catch (error) {
        setErrors([error.message]);
        return;
      }
    }

    if (step < coaSetupWorkflow.length) {
      setStep(step + 1);
      setErrors([]);
    }
  };

  return (
    <div className="wizard-container">
      {/* Step Progress Indicator */}
      <div className="step-progress">
        {coaSetupWorkflow.map((s, i) => (
          <div
            key={i}
            className={`step ${i + 1 === step ? 'active' : ''} ${i + 1 < step ? 'completed' : ''}`}
          >
            <div className="step-number">{s.number}</div>
            <div className="step-title">{s.title}</div>
          </div>
        ))}
      </div>

      {/* Step Content */}
      <div className="step-content">
        <h2>{currentStepConfig.title}</h2>
        <p className="step-description">{currentStepConfig.description}</p>

        {/* Render form fields for this step */}
        <StepForm
          fields={currentStepConfig.requiredFields}
          data={formData}
          onChange={setFormData}
          errors={errors}
        />

        {/* Action Buttons */}
        <div className="step-actions">
          <button
            onClick={() => setStep(step - 1)}
            disabled={step === 1}
          >
            Back
          </button>
          <button
            onClick={handleNext}
            disabled={currentStepConfig.requiredFields.length === 0 && step !== coaSetupWorkflow.length}
          >
            {step === coaSetupWorkflow.length ? 'Create Account' : 'Next'}
          </button>
        </div>
      </div>

      {/* Step Sidebar: Show what will happen next */}
      <div className="step-preview">
        <h3>After This Step</h3>
        {step < coaSetupWorkflow.length && (
          <>
            <p>Next: {coaSetupWorkflow[step].title}</p>
            <p>{coaSetupWorkflow[step].description}</p>
          </>
        )}
      </div>
    </div>
  );
}
```

### 3.2 Multi-Module Setup: Room Type Example

```typescript
// Room Type setup requires linked data from multiple modules
// Frontend prevents creating Room Type without required prerequisites

interface RoomTypeSetup {
  basic: {
    name: string;
    capacity: number;
    floor_plan?: string;
  };
  amenities: string[];      // Selected amenities
  pricing: {
    rate_code_ids: string[]; // Must create rate codes first
    base_price: number;
  };
  accounting: {
    revenue_account_id: string;  // Must create COA first
    deposit_account_id: string;
  };
}

// Prerequisites check
async function validateRoomTypeSetupPrerequisites() {
  const checks = await Promise.all([
    api.checkAmenitiesExist(),
    api.checkRateCodesExist(),
    api.checkCOAAccountsExist(['revenue', 'deposit'])
  ]);

  const [amenitiesOk, rateCodesOk, coaOk] = checks;

  if (!amenitiesOk) {
    return {
      ok: false,
      message: 'Please create amenities first',
      action: 'Go to Settings > Amenities'
    };
  }

  if (!rateCodesOk) {
    return {
      ok: false,
      message: 'Please create rate codes first',
      action: 'Go to Settings > Rate Codes'
    };
  }

  if (!coaOk) {
    return {
      ok: false,
      message: 'Please create COA accounts (revenue, deposit)',
      action: 'Go to Accounting > Chart of Accounts'
    };
  }

  return { ok: true };
}

// In UI: If prerequisites missing, show helpful message + link
function RoomTypeSetupPage() {
  const [prerequisites, setPrerequisites] = useState(null);

  useEffect(() => {
    validateRoomTypeSetupPrerequisites().then(setPrerequisites);
  }, []);

  if (prerequisites && !prerequisites.ok) {
    return (
      <Alert variant="warning">
        <AlertTitle>{prerequisites.message}</AlertTitle>
        <AlertDescription>
          <a href={prerequisites.action} className="link">
            {prerequisites.action}
          </a>
        </AlertDescription>
      </Alert>
    );
  }

  return <RoomTypeForm />;
}
```

---

## 4. Settings UI with Impact Preview

### 4.1 Preview Pattern

Settings should not just change values; they should show **visual preview** of impact before saving.

```typescript
interface SettingConfig {
  id: string;
  label: string;
  description: string;
  type: 'select' | 'number' | 'text' | 'toggle' | 'color';
  currentValue: any;
  options?: any[];
  preview?: {
    type: 'calculation' | 'template' | 'mockup';
    calculate: (newValue: any) => string | ReactNode;
  };
}

// Example: Tax Rate Setting with Pricing Preview
const taxRateSetting: SettingConfig = {
  id: 'tax_rate',
  label: 'Default Tax Rate (%)',
  description: 'Applied to all new transactions',
  type: 'number',
  currentValue: 10,
  preview: {
    type: 'calculation',
    calculate: (newRate) => {
      const basePrice = 100000;
      const taxAmount = basePrice * (newRate / 100);
      const totalPrice = basePrice + taxAmount;

      return `
        Base Price: Rp ${basePrice.toLocaleString()}
        Tax (${newRate}%): Rp ${taxAmount.toLocaleString()}
        ──────────────────────
        Total: Rp ${totalPrice.toLocaleString()}
      `;
    }
  }
};

// Example: Currency Setting with Locale Preview
const currencySetting: SettingConfig = {
  id: 'currency',
  label: 'Currency',
  description: 'Affects display format across the system',
  type: 'select',
  currentValue: 'IDR',
  options: [
    { value: 'IDR', label: '🇮🇩 Indonesian Rupiah' },
    { value: 'USD', label: '🇺🇸 US Dollar' },
    { value: 'SGD', label: '🇸🇬 Singapore Dollar' }
  ],
  preview: {
    type: 'mockup',
    calculate: (newCurrency) => {
      const amount = 1000000;
      const formatters = {
        IDR: new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR' }),
        USD: new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }),
        SGD: new Intl.NumberFormat('en-SG', { style: 'currency', currency: 'SGD' })
      };

      return `Preview: ${formatters[newCurrency].format(amount)}`;
    }
  }
};

// React Component
function SettingEditor({ setting }: { setting: SettingConfig }) {
  const [tempValue, setTempValue] = useState(setting.currentValue);
  const [preview, setPreview] = useState<string | ReactNode>('');

  const handleChange = (newValue: any) => {
    setTempValue(newValue);
    if (setting.preview) {
      setPreview(setting.preview.calculate(newValue));
    }
  };

  return (
    <div className="setting-editor">
      <div className="setting-control">
        <label>{setting.label}</label>
        <p className="help-text">{setting.description}</p>

        {setting.type === 'select' && (
          <select value={tempValue} onChange={(e) => handleChange(e.target.value)}>
            {setting.options?.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        )}

        {setting.type === 'number' && (
          <input
            type="number"
            value={tempValue}
            onChange={(e) => handleChange(parseFloat(e.target.value))}
          />
        )}
      </div>

      {/* PREVIEW: Show impact of change */}
      {setting.preview && (
        <div className="setting-preview">
          <h4>Preview</h4>
          <div className="preview-content">
            {typeof preview === 'string' ? (
              <pre>{preview}</pre>
            ) : (
              preview
            )}
          </div>
          <p className="preview-note">
            This shows how the change will appear in the system.
          </p>
        </div>
      )}

      <div className="actions">
        <button
          variant="outline"
          onClick={() => setTempValue(setting.currentValue)}
        >
          Cancel
        </button>
        <button
          variant="primary"
          onClick={() => saveSetting(setting.id, tempValue)}
        >
          Save Changes
        </button>
      </div>
    </div>
  );
}
```

---

## 5. Dependency Enforcement

### 5.1 Dependency Chain Definition

```typescript
// Define what data must exist before creating dependent data

interface DependencyRule {
  featureName: string;
  requiredData: {
    entity: string;
    minimumCount: number;
    linkedField: string;
  }[];
  message: string;
  setupLink: string;
}

const dependencyRules: DependencyRule[] = [
  {
    featureName: 'PMS - Room Management',
    requiredData: [
      {
        entity: 'RoomType',
        minimumCount: 1,
        linkedField: 'room_type_id'
      },
      {
        entity: 'Floor',
        minimumCount: 1,
        linkedField: 'floor_id'
      }
    ],
    message: 'Cannot create rooms without room types and floors',
    setupLink: '/settings/room-types'
  },
  {
    featureName: 'PMS - Pricing & Rate Codes',
    requiredData: [
      {
        entity: 'RoomType',
        minimumCount: 1,
        linkedField: 'room_type_id'
      },
      {
        entity: 'RateCode',
        minimumCount: 1,
        linkedField: 'rate_code_id'
      }
    ],
    message: 'Create room types and rate codes before setting up pricing',
    setupLink: '/settings/pricing'
  },
  {
    featureName: 'Accounting - Journal Entry',
    requiredData: [
      {
        entity: 'COA',
        minimumCount: 1,
        linkedField: 'debit_account_id'
      },
      {
        entity: 'COA',
        minimumCount: 2,  // Need at least 2 different accounts
        linkedField: 'credit_account_id'
      }
    ],
    message: 'Cannot create journal entries without chart of accounts',
    setupLink: '/accounting/coa'
  },
  {
    featureName: 'POS - Menu Management',
    requiredData: [
      {
        entity: 'MenuCategory',
        minimumCount: 1,
        linkedField: 'category_id'
      },
      {
        entity: 'COA',
        minimumCount: 1,
        linkedField: 'revenue_account_id'
      }
    ],
    message: 'Create menu categories and link COA accounts first',
    setupLink: '/pos/menu-categories'
  }
];

// Implementation
async function checkDependencies(featureName: string): Promise<{
  canAccess: boolean;
  missingData: string[];
  setupLink: string;
}> {
  const rule = dependencyRules.find(r => r.featureName === featureName);

  if (!rule) {
    return { canAccess: true, missingData: [], setupLink: '' };
  }

  const missing: string[] = [];

  for (const dep of rule.requiredData) {
    const count = await api.countEntities(dep.entity);
    if (count < dep.minimumCount) {
      missing.push(`${dep.entity} (need ${dep.minimumCount}, have ${count})`);
    }
  }

  return {
    canAccess: missing.length === 0,
    missingData: missing,
    setupLink: rule.setupLink
  };
}

// In UI: Check before allowing access
async function FeatureGuard({ featureName, children }) {
  const [canAccess, setCanAccess] = useState(false);
  const [missing, setMissing] = useState<string[]>([]);
  const [setupLink, setSetupLink] = useState('');

  useEffect(() => {
    checkDependencies(featureName).then(result => {
      setCanAccess(result.canAccess);
      setMissing(result.missingData);
      setSetupLink(result.setupLink);
    });
  }, [featureName]);

  if (!canAccess) {
    return (
      <Alert variant="error">
        <AlertTitle>This feature is not yet available</AlertTitle>
        <AlertDescription>
          Please set up the following first:
          <ul>
            {missing.map(m => <li key={m}>{m}</li>)}
          </ul>
          <a href={setupLink} className="button button-primary">
            Complete Setup
          </a>
        </AlertDescription>
      </Alert>
    );
  }

  return children;
}
```

---

## 6. Detailed Examples: Critical Data Masters

### 6.1 Chart of Accounts (COA) - Complete Flow

**Problem**: Wrong COA hierarchy breaks journal entries, reports, and reconciliation.

**Solution**: Multi-step workflow with cascading validation.

```typescript
// Step 1: Verify Parent Account Exists & Matches Type

type CoaType = 'ASSET' | 'LIABILITY' | 'EQUITY' | 'REVENUE' | 'EXPENSE';

interface CoaValidation {
  step: number;
  validate: (data: any) => Promise<{
    valid: boolean;
    errors?: string[];
  }>;
}

const coaValidationSteps: CoaValidation[] = [
  {
    step: 1,
    validate: async (data) => {
      const errors = [];

      // Check: Parent exists
      const parent = await api.getCOAById(data.parent_id);
      if (!parent) {
        errors.push('Parent account does not exist');
        return { valid: false, errors };
      }

      // Check: Parent is same type as current
      if (parent.type !== data.type) {
        errors.push(`Parent is ${parent.type} but current is ${data.type}`);
        return { valid: false, errors };
      }

      // Check: Parent is not a leaf node (must be header for having children)
      // Some systems enforce: header accounts can have children, detail accounts cannot
      if (!parent.is_header) {
        errors.push('Parent account must be a header account to have sub-accounts');
        return { valid: false, errors };
      }

      return { valid: errors.length === 0, errors };
    }
  },
  {
    step: 2,
    validate: async (data) => {
      const errors = [];

      // Check: Code is unique
      const existing = await api.getCOAByCode(data.code);
      if (existing) {
        errors.push(`Code ${data.code} already exists`);
        return { valid: false, errors };
      }

      // Check: Code format matches type rules
      const codeRules = {
        'ASSET': /^1\d{3,5}$/,        // 1xxx
        'LIABILITY': /^2\d{3,5}$/,    // 2xxx
        'EQUITY': /^3\d{3,5}$/,       // 3xxx
        'REVENUE': /^4\d{3,5}$/,      // 4xxx
        'EXPENSE': /^5\d{3,5}$/       // 5xxx
      };

      if (!codeRules[data.type].test(data.code)) {
        errors.push(`Code ${data.code} does not match ${data.type} prefix rules`);
        return { valid: false, errors };
      }

      return { valid: errors.length === 0, errors };
    }
  },
  {
    step: 3,
    validate: async (data) => {
      // No sub-accounts can be created under a detail account
      if (!data.is_header) {
        const hasChildren = await api.checkCOAHasChildren(data.id);
        if (hasChildren) {
          return {
            valid: false,
            errors: ['Detail accounts cannot have sub-accounts. Mark as header first.']
          };
        }
      }

      return { valid: true };
    }
  }
];

// Form UI Implementation
function CoaCreationForm() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    type: null,
    parent_id: null,
    code: '',
    name: '',
    is_header: false,
    sub_type: null
  });
  const [parentOptions, setParentOptions] = useState([]);

  // When type changes, fetch matching parents
  const handleTypeChange = async (newType: CoaType) => {
    setFormData({ ...formData, type: newType, parent_id: null });

    // Fetch only parents of this type that are headers
    const parents = await api.getCOAByTypeAndIsHeader(newType, true);
    setParentOptions(
      parents.map(p => ({
        value: p.id,
        label: `${p.code} - ${p.name}`,
        children: p.children_count
      }))
    );
  };

  const handleParentChange = (parentId: string) => {
    setFormData({ ...formData, parent_id: parentId });

    // Show helper text about parent
    const parent = parentOptions.find(p => p.value === parentId);
    console.log(`Selected parent: ${parent.label} (${parent.children} children)`);
  };

  return (
    <div className="coa-form">
      <div className="form-section">
        <h3>Step 1: Account Hierarchy</h3>
        <p>Select account type and parent account</p>

        <select
          value={formData.type || ''}
          onChange={(e) => handleTypeChange(e.target.value as CoaType)}
        >
          <option value="">-- Select Account Type --</option>
          <option value="ASSET">Asset</option>
          <option value="LIABILITY">Liability</option>
          <option value="EQUITY">Equity</option>
          <option value="REVENUE">Revenue</option>
          <option value="EXPENSE">Expense</option>
        </select>

        {formData.type && (
          <select
            value={formData.parent_id || ''}
            onChange={(e) => handleParentChange(e.target.value)}
          >
            <option value="">-- Select Parent Account --</option>
            {parentOptions.map(p => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        )}
      </div>

      {formData.type && formData.parent_id && (
        <div className="form-section">
          <h3>Step 2: Account Details</h3>

          <input
            type="text"
            placeholder="Code (e.g., 1010)"
            value={formData.code}
            onChange={(e) => setFormData({ ...formData, code: e.target.value })}
            pattern={codeRules[formData.type].source}
            title={`Code must start with ${formData.type[0]} (e.g., 1xxx for ASSET)`}
          />

          <input
            type="text"
            placeholder="Account Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          />

          <label>
            <input
              type="checkbox"
              checked={formData.is_header}
              onChange={(e) => setFormData({ ...formData, is_header: e.target.checked })}
            />
            This is a header account (can have sub-accounts)
          </label>
        </div>
      )}

      <button onClick={() => submitCOA(formData)}>Create Account</button>
    </div>
  );
}
```

### 6.2 Room Type - Multi-Module Integration

**Problem**: Room Type setup incomplete → Room rate missing → Can't sell rooms → Inventory wrong.

```typescript
// Room Type creation requires linked setup across 4 modules

interface RoomTypeData {
  // PMS Module
  basic: {
    name: string;
    short_code: string;
    capacity_standard: number;
    capacity_max: number;
    sqm: number;
  };

  // Inventory Module
  inventory: {
    default_cogs_account_id: string;  // Link to COA
  };

  // Accounting Module
  accounting: {
    revenue_account_id: string;       // Link to COA
    deposit_account_id: string;       // Link to COA
  };

  // POS Module (optional, for in-room mini bar)
  pos?: {
    menu_category_id: string;
  };
}

// Validation: Check all prerequisites
async function validateRoomTypePrerequisites() {
  const [coaExists, hasCOA] = await Promise.all([
    api.checkCOAExists(),
    api.countCOA()
  ]);

  if (hasCOA < 4) {  // Need at least: Assets, Revenue, Expense, Liability
    return {
      ok: false,
      blocking: true,
      message: 'Insufficient Chart of Accounts',
      fix: 'Create at least revenue and liability accounts in Accounting > COA'
    };
  }

  return { ok: true };
}

// Multi-step form
function RoomTypeSetupWizard() {
  const [step, setStep] = useState(1);
  const [data, setData] = useState<RoomTypeData>({
    basic: { name: '', short_code: '', capacity_standard: 0, capacity_max: 0, sqm: 0 },
    inventory: { default_cogs_account_id: '' },
    accounting: { revenue_account_id: '', deposit_account_id: '' }
  });

  const steps = [
    { title: 'Basic Information', fields: ['basic'] },
    { title: 'Accounting Links', fields: ['accounting'] },
    { title: 'Inventory Links', fields: ['inventory'] },
    { title: 'Review & Create', fields: [] }
  ];

  return (
    <div>
      {/* Step 1: Basic Info */}
      {step === 1 && (
        <div>
          <input
            placeholder="Room Type Name"
            value={data.basic.name}
            onChange={(e) => setData({
              ...data,
              basic: { ...data.basic, name: e.target.value }
            })}
          />
          {/* More fields... */}
        </div>
      )}

      {/* Step 2: Accounting Links - with validation */}
      {step === 2 && (
        <div>
          <label>
            Revenue Account *
            <select
              value={data.accounting.revenue_account_id}
              onChange={(e) => setData({
                ...data,
                accounting: { ...data.accounting, revenue_account_id: e.target.value }
              })}
            >
              <option value="">-- Select Revenue Account --</option>
              {/* Populated from COA filtered by type=REVENUE */}
            </select>
          </label>

          <label>
            Deposit Account *
            <select
              value={data.accounting.deposit_account_id}
              onChange={(e) => setData({
                ...data,
                accounting: { ...data.accounting, deposit_account_id: e.target.value }
              })}
            >
              <option value="">-- Select Liability/Deposit Account --</option>
              {/* Populated from COA filtered by type=LIABILITY */}
            </select>
          </label>

          <Alert>
            Selected accounts will be used for all revenue recognition and deposit tracking
            for this room type.
          </Alert>
        </div>
      )}

      {/* Step 3: Inventory Links */}
      {step === 3 && (
        <div>
          <label>
            Default COGS Account *
            <select value={data.inventory.default_cogs_account_id}>
              {/* Populated from COA filtered by type=EXPENSE */}
            </select>
          </label>
        </div>
      )}

      {/* Step 4: Review */}
      {step === 4 && (
        <div className="review">
          <h3>Summary</h3>
          <dl>
            <dt>Room Type Name:</dt>
            <dd>{data.basic.name}</dd>
            <dt>Revenue Account:</dt>
            <dd>{getAccountLabel(data.accounting.revenue_account_id)}</dd>
            <dt>Deposit Account:</dt>
            <dd>{getAccountLabel(data.accounting.deposit_account_id)}</dd>
            <dt>COGS Account:</dt>
            <dd>{getAccountLabel(data.inventory.default_cogs_account_id)}</dd>
          </dl>
          <button onClick={() => createRoomType(data)}>Create Room Type</button>
        </div>
      )}

      <div className="actions">
        <button onClick={() => setStep(step - 1)} disabled={step === 1}>Back</button>
        <button onClick={() => setStep(step + 1)} disabled={step === 4}>Next</button>
      </div>
    </div>
  );
}
```

### 6.3 Menu Item (POS) - Input Constraints

```typescript
// Menu Item must be linked to multiple data:
// - Category (POS)
// - Revenue Account (Accounting)
// - Tax Treatment (Accounting)
// - Ingredient/Recipe (Inventory)

interface MenuItemData {
  name: string;
  category_id: string;
  price: number;
  tax_treatment: 'taxable' | 'exempt' | 'zero_rated';
  revenue_account_id: string;
  cogs_account_id: string;
}

// Dynamic field rules
const menuItemFormRules = {
  // Tax field options depend on region setting
  tax_treatment: {
    visible: true,
    options: async () => {
      const region = await api.getCompanyRegion();
      return region === 'ID'
        ? [
            { value: 'taxable', label: 'PPN 10%' },
            { value: 'exempt', label: 'Exempt (PPN 0%)' },
            { value: 'zero_rated', label: 'Zero Rated (Export)' }
          ]
        : [
            { value: 'taxable', label: 'With Tax' },
            { value: 'exempt', label: 'Exempt' }
          ];
    }
  },

  // Revenue account must be REVENUE type only
  revenue_account_id: {
    visible: true,
    options: async () => {
      const accounts = await api.getCOAByType('REVENUE');
      return accounts.map(a => ({
        value: a.id,
        label: `${a.code} - ${a.name}`
      }));
    }
  },

  // COGS account must be EXPENSE type only
  cogs_account_id: {
    visible: true,
    options: async () => {
      const accounts = await api.getCOAByType('EXPENSE');
      return accounts.map(a => ({
        value: a.id,
        label: `${a.code} - ${a.name}`
      }));
    }
  },

  // Category must exist
  category_id: {
    visible: true,
    disabled: async () => {
      const count = await api.countMenuCategories();
      return count === 0;
    },
    help: (formState) => {
      if (!formState.category_id) {
        return 'Select menu category first';
      }
    }
  }
};
```

---

## 7. Implementation Checklist

- [ ] **Form Field Configuration**: Define all fields with constraints
- [ ] **Cascading Logic**: Parent field changes trigger child options update
- [ ] **Conditional Visibility**: Show/hide fields based on form state
- [ ] **Prerequisite Checks**: Verify dependencies before allowing feature access
- [ ] **Step-Based Workflow**: Complex setup flows broken into steps
- [ ] **Validation Layer 4**: Backend validates all constraints
- [ ] **Error Messages**: Clear, actionable messages (not just "Invalid!")
- [ ] **Help Text**: Contextual help for each field
- [ ] **Preview**: Show impact of settings before saving
- [ ] **Disable Logic**: Prevent early entry (e.g., can't select child until parent chosen)
- [ ] **Database Constraints**: NOT NULL, UNIQUE, FK, CHECK as last defense
- [ ] **Testing**: Unit tests for validation rules, e2e tests for workflows

---

## 8. Key Takeaway

**"Make it impossible to enter wrong data."**

When your COA is set up correctly with proper hierarchy and constraints, your journal entries will be correct. When your room types are fully configured across all modules, your bookings will work correctly. When your menu items link to correct accounts, your daily reports will be accurate.

**Input validation is the foundation of data integrity.**

