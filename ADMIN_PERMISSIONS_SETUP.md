# Admin Permissions Setup - Panchayath and Wards Management

## Summary
Admin users now have full permissions to add, edit, and delete Panchayaths and their Wards through the Django Admin Interface.

## Changes Made

### 1. Database Models (models.py)
- **Created new `Panchayath` model** with fields:
  - `name`: CharField (unique) - Name of the panchayath/municipality
  - `code`: CharField (unique) - Short code for the panchayath
  - `description`: TextField - Optional description
  - `created_at`: DateTimeField - Auto-set on creation
  - `updated_at`: DateTimeField - Auto-updated on save

- **Updated `Ward` model** to:
  - Replace hardcoded panchayath choices with ForeignKey to `Panchayath`
  - Add `panchayath` ForeignKey field with `related_name='wards'`
  - Remove old `panchayat_municipality` choice field
  - Update Meta with `unique_together` constraint for (panchayath, ward_number)

### 2. Forms (forms.py)
- **Updated all registration forms** (UserRegistrationForm, WorkerRegistrationForm, AdminRegistrationForm):
  - Replaced `panchayat_municipality` ChoiceField with `panchayath` ModelChoiceField
  - Now dynamically loads all Panchayaths from the database
  - Updated imports to include `Panchayath` model

### 3. Admin Interface (admin.py)
Registered all models with comprehensive admin configurations:

#### PanchayathAdmin
- List display: name, code, created_at
- Search by: name, code
- Read-only fields: created_at, updated_at

#### WardAdmin
- List display: name, panchayath, ward_number
- Filter by: panchayath
- Search by: name, panchayath name

#### Additional Admin Registrations
- ProfileAdmin: Users profiles with role filtering
- PickupRequestAdmin: Waste pickup requests with status tracking
- RewardAdmin: User reward points
- PaymentAdmin: Payment records
- FeedbackAdmin: Feedback and complaints management

### 4. Database Migration
- Created migration: `0005_panchayath_alter_ward_options_ward_panchayath_and_more.py`
- Applied all migrations successfully

### 5. Initial Data
Created sample data in the database:

**Panchayaths:**
- Meenichil (MEN)
- Kanjirapally (KAN)
- Kollam (KOL)

**Wards:**
- Meenichil: 5 wards
- Kanjirapally: 4 wards
- Kollam: 6 wards

## How to Use

### Access Admin Panel
1. Log in to Django Admin at `/admin/`
2. Use superuser credentials

### Add a New Panchayath
1. Navigate to **Panchayaths** section
2. Click **+ Add Panchayath**
3. Fill in:
   - Name: The panchayath/municipality name
   - Code: A unique short code (e.g., "MEN")
   - Description: (Optional) Additional details
4. Click **Save**

### Add New Wards
1. Navigate to **Wards** section
2. Click **+ Add Ward**
3. Fill in:
   - Name: Ward name
   - Panchayath: Select the parent panchayath
   - Ward Number: Numeric identifier
4. Click **Save**

### Edit or Delete
- Click on any Panchayath or Ward in the list to edit
- Use the delete action from the list view to remove entries

## Permissions
- Full CRUD permissions for Panchayaths
- Full CRUD permissions for Wards
- Auto-enforced data integrity through unique constraints
- Automatic timestamp tracking

## Benefits
1. **Scalability**: Easy to add new panchayaths and wards
2. **Data Integrity**: Prevents duplicate panchayaths and ward-panchayath combinations
3. **Admin Interface**: User-friendly management without manual database access
4. **Auditability**: Created and updated timestamps track changes
5. **Flexibility**: Supports growth of the system to new areas
