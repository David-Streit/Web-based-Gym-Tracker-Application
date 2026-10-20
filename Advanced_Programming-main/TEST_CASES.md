# Test Cases – Advanced Programming Gym Tracker

## TC_001 – User login with valid credentials

**Description:** Verify that users can log in with valid credentials.

### Preconditions
- Application is running
- User account already exists

### Test steps
1. Open login page
2. Enter valid username
3. Enter valid password
4. Press Login

### Test data/input
Username: testuser  
Password: Test123

### Expected result
User is redirected to dashboard.

### Actual result
User logged in and dashboard displayed.

### Status
Pass

### Comments
No issues found.

---

## TC_002 – Login with invalid password

### Preconditions
- Application running
- Existing user available

### Test steps
1. Open login page
2. Enter username
3. Enter wrong password
4. Press Login

### Test data/input
Username: testuser  
Password: wrong123

### Expected result
Error message shown.

### Actual result
Login denied.

### Status
Pass

### Comments
Password validation works correctly.

---

## TC_003 – Register new account

### Preconditions
- Username does not exist

### Test steps
1. Open registration page
2. Enter account data
3. Press Register

### Test data/input
Username: GeorgeTest  
Password: Gym123

### Expected result
Account created successfully.

### Actual result
User stored in database.

### Status
Pass

---

## TC_004 – Add workout session

### Preconditions
- User logged in

### Test steps
1. Open workout page
2. Enter workout details
3. Save workout

### Test data/input
Muscle: Chest  
Exercise: Bench Press  
Sets: 4  
Reps: 10

### Expected result
Workout appears in history.

### Actual result
Workout stored correctly.

### Status
Pass

---

## TC_005 – Dashboard statistics refresh

### Preconditions
- Workout data exists

### Test steps
1. Add workout
2. Return to dashboard

### Test data/input
Back workout session

### Expected result
Statistics update automatically.

### Actual result
Dashboard updated.

### Status
Pass

---

## TC_006 – Logout

### Preconditions
- User logged in

### Test steps
1. Press Logout button

### Expected result
Return to login page

### Actual result
Session removed

### Status
Pass

---

## TC_007 – Unauthorized access prevention

### Preconditions
- User not logged in

### Test steps
1. Open dashboard URL manually

### Expected result
Redirect to login page

### Actual result
Redirect successful

### Status
Pass

---

## TC_008 – Empty field validation

### Preconditions
Application running

### Test steps
1. Leave fields empty
2. Press login

### Expected result
Validation error displayed

### Actual result
Error shown

### Status
Pass