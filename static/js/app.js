// --- Global ---
let currentOperatorId = null;
let currentOperatorName = null;

document.addEventListener('DOMContentLoaded', () => {
    // Session Restore
    if (sessionStorage.getItem('canteen_role')) {
        currentOperatorId = sessionStorage.getItem('canteen_op_id');
        currentOperatorName = sessionStorage.getItem('canteen_op_user');
    }

    // --- Page Specific Init ---
    const path = window.location.pathname;
    if (path === '/admin') {
        initAdmin();
    } else if (path === '/operator') {
        initOperator();
    } else if (path === '/' || path.endsWith('login.html')) {
        initLogin();
    }
});

function logout() {
    sessionStorage.clear();
    window.location.href = '/';
}

// --- Login Logic ---
function initLogin() {
    if (!document.getElementById('login-username')) return;

    let loginRole = 'operator';
    window.setLoginRole = function (role) {
        loginRole = role;
        document.getElementById('btn-role-operator').classList.toggle('active', role === 'operator');
        document.getElementById('btn-role-admin').classList.toggle('active', role === 'admin');
    }

    window.handleLogin = async function () {
        const user = document.getElementById('login-username').value;
        const pass = document.getElementById('login-password').value;

        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ role: loginRole, username: user, password: pass })
            });
            const data = await res.json();

            if (data.status === 'success') {
                sessionStorage.setItem('canteen_role', data.role);
                if (data.role === 'operator') {
                    sessionStorage.setItem('canteen_op_id', data.id);
                    sessionStorage.setItem('canteen_op_user', data.username);
                    window.location.href = '/operator';
                } else {
                    window.location.href = '/admin';
                }
            } else {
                alert(data.message);
            }
        } catch (e) {
            console.error(e);
            alert("Login failed. Login server error.");
        }
    }
}

// --- Admin Logic (Global) ---

window.showTab = function (tabId) {
    // Toggle Sections
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active-section'));
    const activeEl = document.getElementById(tabId);
    if (activeEl) activeEl.classList.add('active-section');

    // Toggle Tabs
    document.querySelectorAll('.tabs button').forEach(el => el.classList.remove('active'));
    // Try to find the button that called this
    const btn = document.querySelector(`button[onclick="showTab('${tabId}')"]`);
    if (btn) btn.classList.add('active');

    // Load Data
    if (tabId === 'admin-students') loadStudents();
    if (tabId === 'admin-operators') loadOperators();
    if (tabId === 'admin-reports') loadReports();
}

window.addStudent = async function () {
    const id = document.getElementById('edit-std-id').value;
    const name = document.getElementById('new-std-name').value;
    const roll = document.getElementById('new-std-roll').value;
    const status = document.getElementById('new-std-status').value;
    const mode = document.getElementById('new-std-mode').value;
    const branch = document.getElementById('new-std-branch').value || 'General';
    const amount = document.getElementById('new-std-amount').value || 0;

    if (!name) return alert("Enter Student Name");

    try {
        const method = id ? 'PUT' : 'POST';
        const body = {
            name: name,
            roll: roll,
            payment_status: status,
            payment_mode: mode,
            dept: branch,
            amount_paid: amount
        };
        if (id) body.id = id;

        await fetch('/api/students', {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        // Reset form
        document.getElementById('edit-std-id').value = '';
        document.getElementById('new-std-name').value = '';
        document.getElementById('new-std-roll').value = '';
        document.getElementById('new-std-branch').value = '';
        document.getElementById('new-std-amount').value = '';
        document.getElementById('btn-add-student').textContent = 'Add Student';
        document.getElementById('btn-add-student').classList.remove('warning-btn'); // if we use different color for update

        loadStudents();
    } catch (e) { alert("Error saving student: " + e); }
}

window.editStudent = function (student) {
    // Populate form
    document.getElementById('edit-std-id').value = student.id;
    document.getElementById('new-std-name').value = student.name;
    document.getElementById('new-std-roll').value = student.roll || '';
    document.getElementById('new-std-branch').value = student.dept || '';
    document.getElementById('new-std-status').value = student.payment_status;
    document.getElementById('new-std-mode').value = student.payment_mode;
    document.getElementById('new-std-amount').value = student.amount_paid || 0;

    // Change button
    const btn = document.getElementById('btn-add-student');
    btn.textContent = 'Update Student';
    btn.scrollIntoView({ behavior: 'smooth' });
}

window.deleteStudent = async function (id) {
    console.log("Delete Requested for ID:", id);
    if (confirm("Confirm: Delete student ID " + id + "?")) {
        try {
            const res = await fetch(`/api/students?id=${id}`, { method: 'DELETE' });
            if (res.ok) {
                // Check if we were editing this one
                if (document.getElementById('edit-std-id').value == id) {
                    // Reset form
                    document.getElementById('edit-std-id').value = '';
                    document.getElementById('btn-add-student').textContent = 'Add Student';
                }
                alert("Success: Student deleted.");
                loadStudents();
            } else {
                const err = await res.text();
                alert("Failed: Server returned " + res.status + "\n" + err);
            }
        } catch (e) {
            console.error(e);
            alert("Network Error during delete: " + e);
        }
    }
}

window.addOperator = async function () {
    const user = document.getElementById('new-op-user').value;
    const pass = document.getElementById('new-op-pass').value;
    if (!user || !pass) return alert("Fill details");

    try {
        await fetch('/api/operators', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass })
        });
        document.getElementById('new-op-user').value = '';
        document.getElementById('new-op-pass').value = '';
        loadOperators();
    } catch (e) { alert("Error adding operator: " + e); }
}

window.deleteOperator = async function (id) {
    if (confirm("Delete Operator ID " + id + "?")) {
        try {
            const res = await fetch(`/api/operators?id=${id}`, { method: 'DELETE' });
            if (res.ok) {
                alert("Operator Deleted");
                loadOperators();
            } else {
                alert("Delete Failed");
            }
        } catch (e) { alert("Error deleting operator: " + e); }
    }
}

window.exportCSV = function () {
    window.location.href = '/api/export';
}

window.updateExcel = async function () {
    try {
        const btn = document.querySelector('button[onclick="updateExcel()"]');
        const originalText = btn.textContent;
        btn.textContent = "Updating...";
        btn.disabled = true;

        const res = await fetch('/api/backup/excel', { method: 'POST' });
        const data = await res.json();

        if (data.status === 'success') {
            alert("Success: " + data.message);
        } else {
            alert("Error: " + data.message);
        }
        btn.textContent = originalText;
        btn.disabled = false;
    } catch (e) {
        alert("Network Error: " + e);
    }
}

async function loadStudents() {
    try {
        const res = await fetch('/api/students', { cache: 'no-store' });
        const data = await res.json();
        const tbody = document.getElementById('admin-students-list');
        if (tbody) {
            tbody.innerHTML = '';
            data.forEach((s, index) => {
                // Serialize object for edit function
                const sData = JSON.stringify(s).replace(/"/g, "&quot;");
                tbody.innerHTML += `
                    <tr>
                        <td>${index + 1} (ID: ${s.id})</td>
                        <td>${s.name}</td>
                        <td>${s.roll || '-'}</td>
                        <td>${s.dept || '-'}</td>
                        <td>B:${s.breakfast_count} / L:${s.lunch_count} / D:${s.dinner_count}</td>
                        <td>${s.payment_status} (${s.payment_mode})</td>
                        <td>₹${s.amount_paid || 0}</td>
                        <td>
                            <button onclick="window.editStudent(${sData})" class="primary-btn" style="padding: 5px 10px; font-size: 0.8em;">Edit</button>
                            <button onclick="window.deleteStudent(${s.id})" class="danger-btn" style="padding: 5px 10px; font-size: 0.8em;">Delete</button>
                        </td>
                    </tr>
                `;
            });
        }
    } catch (e) { console.error("Load Students Fault", e); }
}

async function loadOperators() {
    try {
        const res = await fetch('/api/operators', { cache: 'no-store' });
        const data = await res.json();
        const tbody = document.getElementById('admin-operators-list');
        if (tbody) {
            tbody.innerHTML = '';
            data.forEach(op => {
                tbody.innerHTML += `
                    <tr>
                        <td>${op.id}</td>
                        <td>${op.username}</td>
                        <td><button onclick="window.deleteOperator(${op.id})" class="danger-btn">Delete</button></td>
                    </tr>
                `;
            });
        }
    } catch (e) { console.error("Load Operators Fault", e); }
}

async function loadReports() {
    try {
        const res = await fetch('/api/reports/meals');
        const stats = await res.json();
        const div = document.getElementById('admin-meal-stats');
        if (div) {
            let html = '<ul>';
            for (const [meal, count] of Object.entries(stats)) {
                html += `<li><strong>${meal}:</strong> ${count}</li>`;
            }
            html += '</ul>';
            div.innerHTML = html;
        }
    } catch (e) { console.error("Load Reports Fault", e); }
}

function initAdmin() {
    // Guard
    if (sessionStorage.getItem('canteen_role') !== 'admin') {
        window.location.href = '/';
        return;
    }
    // Load initial
    showTab('admin-students');

    // Search Listener
    const searchInput = document.getElementById('admin-student-search');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('#admin-students-list tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(term) ? '' : 'none';
            });
        });
    }
}


// --- Operator Logic ---
function initOperator() {
    if (sessionStorage.getItem('canteen_role') !== 'operator') {
        window.location.href = '/';
        return;
    }

    const opName = sessionStorage.getItem('canteen_op_user');
    if (opName && document.getElementById('op-username-display')) {
        document.getElementById('op-username-display').textContent = opName;
    }

    loadOperatorData();

    // Event Listeners for search
    const searchInput = document.getElementById('bill-student-search');
    if (searchInput) {
        searchInput.addEventListener('change', handleStudentSearch);
        searchInput.addEventListener('input', handleStudentSearch);
    }
}
// (Functions for operator like generateBill kept global or attached to window if needed, or defined here)
// Currently initOperator logic was defining them on window. Let's make them global to be safe.

window.toggleUserType = function () {
    const type = document.querySelector('input[name="userType"]:checked').value;
    if (type === 'hostel') {
        const h = document.getElementById('input-hostel'); if (h) h.classList.remove('hidden');
        const s = document.getElementById('input-staff'); if (s) s.classList.add('hidden');
        const n = document.getElementById('input-normal'); if (n) n.classList.add('hidden');
    } else if (type === 'staff') {
        const h = document.getElementById('input-hostel'); if (h) h.classList.add('hidden');
        const s = document.getElementById('input-staff'); if (s) s.classList.remove('hidden');
        const n = document.getElementById('input-normal'); if (n) n.classList.add('hidden');
    } else {
        const h = document.getElementById('input-hostel'); if (h) h.classList.add('hidden');
        const s = document.getElementById('input-staff'); if (s) s.classList.add('hidden');
        const n = document.getElementById('input-normal'); if (n) n.classList.remove('hidden');
    }
}

window.generateBill = async function () {
    const userType = document.querySelector('input[name="userType"]:checked').value;
    const meal = document.getElementById('bill-meal-type').value;
    const amount = document.getElementById('bill-amount').value;
    const mode = document.getElementById('bill-payment-mode').value;

    let studentId = null;
    let guestName = null;

    if (userType === 'hostel') {
        studentId = document.getElementById('bill-student-id').value;
        if (!studentId) {
            const val = document.getElementById('bill-student-search').value;
            const match = val.match(/\[ID: (\d+)\]/);
            if (match) studentId = match[1];
        }
        if (!studentId) return alert("Select a valid student.");
    } else if (userType === 'staff') {
        guestName = document.getElementById('bill-staff-name').value;
        if (!guestName) return alert("Enter Staff Name.");
    } else {
        guestName = document.getElementById('bill-guest-name').value || "Guest";
    }

    try {
        const res = await fetch('/api/bill', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_type: userType,
                student_id: studentId,
                guest_name: guestName,
                meal_type: meal,
                amount: amount,
                payment_mode: mode,
                operator_id: currentOperatorId
            })
        });
        const data = await res.json();
        if (data.status === 'success') {
            const width = 400; const height = 600;
            const left = (screen.width - width) / 2;
            const top = (screen.height - height) / 2;
            window.open(`/bill-view/${data.bill_no}`, 'BillPrint', `width=${width},height=${height},top=${top},left=${left}`);

            // Clear inputs
            if (userType === 'normal') document.getElementById('bill-guest-name').value = '';
            if (userType === 'staff') document.getElementById('bill-staff-name').value = '';
            if (userType === 'hostel') {
                document.getElementById('bill-student-search').value = '';
                document.getElementById('bill-student-id').value = '';
            }
            loadLiveStats();
        } else {
            alert("Error: " + data.message);
        }
    } catch (e) { console.error(e); alert("Network Error"); }
}

async function loadOperatorData() {
    try {
        const res = await fetch('/api/students');
        const data = await res.json();
        const datalist = document.getElementById('student-list');
        if (datalist) {
            datalist.innerHTML = '';
            data.forEach(s => {
                const opt = document.createElement('option');
                // Improved format: Name (Roll: X) [ID: Y]
                const rollStr = s.roll ? `Roll: ${s.roll}` : 'No Roll';
                opt.value = `${s.name} (${rollStr}) [ID: ${s.id}]`;
                datalist.appendChild(opt);
            });
        }
        loadLiveStats();
    } catch (e) { console.error("Op Data Error", e); }
}

function handleStudentSearch(e) {
    const val = e.target.value;
    // Match [ID: 123]
    const match = val.match(/\[ID: (\d+)\]/);
    if (match) {
        document.getElementById('bill-student-id').value = match[1];
    } else {
        document.getElementById('bill-student-id').value = '';
    }
}

async function loadLiveStats() {
    try {
        const res = await fetch('/api/reports/meals');
        const stats = await res.json();
        const div = document.getElementById('op-meal-stats');
        if (div) {
            let html = '';
            for (const [meal, count] of Object.entries(stats)) {
                html += `<div>${meal}: ${count}</div>`;
            }
            div.innerHTML = html || 'No meals served.';
        }
    } catch (e) { console.error("Stats Error", e); }
}
